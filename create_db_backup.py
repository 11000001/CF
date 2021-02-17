import subprocess

def create_db_backup():
	cmd = 'manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission --indent 4'
	try:
		f = open("db_dump.json", "w", encoding="utf-8")
		p = subprocess.run(cmd, capture_output=True, text=True, shell=True)
		f.write(p.stdout)
	finally:
		f.close()

if __name__ == '__main__':
	create_db_backup()