#!/usr/bin/env python

import sys
import MySQLdb
import getpass
import time

class SqlPerf:
	def parse_args(self):
		args = ['-u', '-p', '-h', '-d', '-c']
		try:
			if sys.argv.index('--help'):
				print "Usage: mysqlperf -u <user> -p <password> -h <host> -c <count> <dbname>"
				sys.exit(0)
		except ValueError:
			None
		self.params = {
			'-h': 'localhost',
			'-u': 'root',
			'-p': True,
			'-d': '',
			'-c': 1000,
		}
		argv = sys.argv
                if len(argv) > 0:
                        self.params['-d'] = argv.pop(-1)
		for arg in args:
			try:
				index = argv.index(arg)
				if len(argv) > index and argv[index + 1][:1] != '-':
					self.params[arg] = argv[index + 1]
				else:
					self.params[arg] = True
			except:
				None

	def user_input(self):
		try:
			if self.params['-p'] is True:
				self.params['-p'] = getpass.getpass()
		except:
			print 'Have not password'
			sys.exit(0)
		try:
			self.params['q1'] = raw_input('Query #1: ')
			self.params['q2'] = raw_input('Query #2: ')
		except:
			print 'Have not queries'
			sys.exit(0)

	def compare(self):
		self.con = MySQLdb.connect(host=self.params['-h'], user=self.params['-u'],
			passwd=self.params['-p'], db=self.params['-d'])
		print "\nRunning query 1..."
		self.q1 = self.run(self.params['q1'])
		print "Running query 2..."
		self.q2 = self.run(self.params['q2'])
		self.print_result()

	def run(self, query):
		cursor = self.con.cursor()
		start = time.time()
		for i in range(1, int(self.params['-c'])):
			cursor.execute(query)
		end = time.time()
		return {
				'start': start,
				'end':   end,
				'time':  (end - start)
			}

	def print_result(self):
		print 'Query #1: ', self.q1['time'], '/', (self.q1['time']/int(self.params['-c']))
		print 'Query #2: ', self.q2['time'], '/', (self.q2['time']/int(self.params['-c']))

if __name__ == "__main__":
	s = SqlPerf()
	s.parse_args()
	s.user_input()
	s.compare()

