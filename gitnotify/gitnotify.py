#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gobject
import gtk
import sys
import os
import re
import subprocess
import pynotify
import threading
from configobj import ConfigObj

try:
	import pynotify
	if not pynotify.init('Git Notify'):
		raise Exception
except:
	print "cannot init pynotify"
	sys.exit(0)

class GitManager():
	def __init__(self, parent):
		self._parent = parent

	def pull(self, widget=None):
		output = self.runProcess('git pull')
		self._parent.hide_button('pull')
		self.notify('pull status', output.strip())

	def push(self, widget=None):
		output = self.runProcess('git push')
		self._parent.hide_button('push')
		self.notify('push status', output.strip())

	def get_commits(self, repo='', lastcommit=''):
		if repo == 'origin':
			self.runProcess('git fetch origin')
			output = self.runProcess('git log origin/master -n 10 --pretty=short')
		else:
			output = self.runProcess('git log -n 10 --pretty=short')

		commits = re.findall(r'commit ([^\n]+)', output)
		authors = re.findall(r'Author: ([^\n]+)', output)
		i = -1
		infos = None
		for line in output.split('\n'):
			if line.find('commit') != -1:
				i = i+1
			else:
				if line.find('Author:') != -1 or line.find('Merge:') != -1 or line.strip() == '':
					continue
				if infos == None:
					infos = [line.strip() + "\n"]
				elif len(infos) > i:
					infos[i] += line.strip() + "\n"
				else:
					infos += [line.strip() + "\n"]
		result = []
		if commits[0] != lastcommit:
			try:
				index = commits.index(lastcommit)
			except:
				index = len(commits)
#			for commit in commits[0:index]:
			for commit in commits[0:5]:
				i = commits.index(commit)
				result += [{
						'commit': commit,
						'author': authors[i].strip(),
						'description': infos[i].strip(),
					}]
				#i = commits.index(commit)
				#n = pynotify.Notification("Commit by " + authors[i].strip(), infos[i].strip())
                		#n.show()
				#print 'pushing %s' % commit
			#print 'setting config to %s' % commits[0]
			#self._parent.set_config('commit', commits[0])
			return result

	def runProcess(self, command):
		p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		result = ''
		while (True):
			retcode = p.poll()
			result += p.stdout.readline()
			if (retcode is not None):
				try:
					p.kill()
				except:
					None
				return result

	def get_local_commits(self):
		return self.get_commits()

	def get_origin_commits(self):
		return self.get_commits('origin')

	def get_cross_commit(self):
		local = self.get_local_commits()
		origin = self.get_origin_commits()
		ahead = ''
		commits = []
		try:

			if local[0]['commit'] == origin[0]['commit']:
				return ('up', None)

			m = min(len(local), len(origin))

			for i in range(1, m):
				for o in range(0, i):
					if local[i]['commit'] == origin[o]['commit']:
						ahead = 'local'
						commits = local[0:i]
						raise
					if origin[i]['commit'] == local[o]['commit']:
						ahead = 'origin'
						commits = origin[0:i]
						raise

		except Exception as e:
			#print e
			None
		#if ahead != '' and commit:
		return (ahead, commits)

	def check(self):
		ahead, commits = self.get_cross_commit()
		if ahead == 'local':
			self._parent.show_button('push')
			self._parent.set_status('Your branch is %s commit(s) ahead' % str(len(commits)))
			self.notify('Git Status', 'Your branch is ahead of \'origin/master\' by %s commit(s).' % str(len(commits)))
		elif ahead == 'origin':
			self._parent.show_button('pull')
			self._parent.set_status('%s new commit(s). Need to update' % str(len(commits)))
			self.notify('Git commit by ' + commits[0]['author'],
				commits[0]['description'])
		elif ahead == 'up':
			self._parent.set_status('already up-to-date')
		#else:
		#	print 'not found'

	def notify(self, title, message):
		n = pynotify.Notification(title, message)
		n.show()


class TaskThread(threading.Thread):
	"""Thread that executes a task every N seconds"""

	def __init__(self, parent):
		threading.Thread.__init__(self)
		self._finished = threading.Event()
		self._interval = 10.0
		self._parent = parent
		self._manager = GitManager(self._parent)

	def lastcommit(self):
		try:
			return self._parent.get_config('commit')
		except:
			return None

	def manager(self):
		return self._manager

	def setInterval(self, interval):
		"""Set the number of seconds we sleep between executing our task"""
		self._interval = interval

	def setParent(self, parent):
		self._parent = parent

	def shutdown(self):
		"""Stop this thread"""
		self._finished.set()

	def run(self):
		while 1:
			if self._finished.isSet(): return
			self._manager.check()

			# sleep for interval or until shutdown
			self._finished.wait(self._interval)

	def task(self):
		None

	def runProcess(self, command):
		None


class MainWindow:
	def __init__(self, tray):
		self.tray = tray
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_position(gtk.WIN_POS_CENTER)
		self.window.connect('destroy', self.destroy)
		self.window.set_border_width(10)
		self.window.show()
		self.button = gtk.Button('Save')
		self.button.connect('clicked', self.save, None)
		self.window.add(self.button)
		self.button.show()
		self.show()

	def show(self):
		return self.window.set_visible(True)

	def destroy(self, widget, data=None):
		return self.window.set_visible(False)
		try:
			self.window.destroy_with_parent()
		except:
			return False

	def save(self, widget, data=None):
		self.tray.config['timer'] = 30
		self.tray.config['git_dir'] = ''
		self.tray.config.write()
		self.tray.start()

class TrayIcon:
	def __init__(self):
		self.menu = gtk.Menu()
		self.quit_button = gtk.MenuItem('Quit')
		self.quit_button.connect('activate', self.quit)
		self.menu.append(self.quit_button)
		self.quit_button.show()
		self.icon = gtk.status_icon_new_from_file('icon.png')
		#self.icon.connect('activate', self.show)
		self.icon.connect('popup-menu', self.icon_clicked)
		self.set_status('waiting...')

		self.load_config()

		if self.get_config('git_dir') and self.get_config('timer'):
			self.start()
		else:
			print 'not configured'
			sys.exit(0)
			#self.show(None)
		gobject.threads_init()
		gtk.gdk.threads_init()
		gtk.main()

	def load_config(self):
		home_dir = os.path.expanduser('~')
		self.config = ConfigObj(home_dir + '/.gitnotify')
		if self.get_config('git_dir'):
			os.chdir(self.get_config('git_dir'))

	def set_config(self, param, value):
		try:
			self.config[param] = value
			self.config.write()
		except:
			return False

	def get_config(self, param):
		try:
			return self.config[param]
		except:
			return None

	def set_status(self, status):
		try:
			self.icon.set_tooltip_text(status)
		except:
			None

	def show_button(self, button):

		if button == 'push':
			try:
				if self.push_button:
					self.push_button.show()
			except:
				self.push_button = gtk.MenuItem('Push')
				self.push_button.connect('activate', self.timer._manager.push)
				self.menu.append(self.push_button)
				self.push_button.show()

		elif button == 'pull':
			try:
				if self.pull_button:
					self.pull_button.show()
			except:
				self.pull_button = gtk.MenuItem('Pull')
				self.pull_button.connect('activate', self.timer._manager.pull)
				self.menu.append(self.pull_button)
				self.pull_button.show()

	def hide_button(self, button):
		try:
			if button == 'push':
				self.push_button.hide()
			elif button == 'pull':
				self.pull_button.hide()
		except:
			None

	def stop(self):
		if self.timer:
			self.timer.cancel()
			
	def start(self):
		#self.timer = threading.Timer(float(self.get_config('timer')), self.timer)
		#self.timer.start()
		self.timer = TaskThread(self)
		self.timer.setInterval(float(self.get_config('timer')))
		self.timer.start()


	#def timer(self):
	#	# check git updates
	#	n = pynotify.Notification("Test 1", "Message for test1")
	#	n.show()

	def icon_clicked(self, status, button, time):
		self.menu.popup(None, None, None, button, time)

	def show(self, widget):
		try:
			if self.window:
				self.window.show()
		except:
			self.window = MainWindow(self)

	def quit(self, widget):
		try:
			if self.timer:
				#self.timer.cancel()
				self.timer.shutdown()
		except:
			None
		sys.exit(0)


if __name__ == "__main__":
	tray = TrayIcon()
		
