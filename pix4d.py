import subprocess as s, sys

def create_project(proj_name, image_dir, email, password, pix4dexe = '"C:\Program Files\Pix4Dmapper\pix4dmapper.exe"'):
	pixcmd = [pix4dexe, "--email "+email, "--password "+password, "-c -n --image-dir "+image_dir, proj_name]
	pixcmd = " ".join(pixcmd)
	#print(pixcmd)
	s.call(pixcmd,shell=True)
	
def create(proj_name, template, image_dir, pix4dexe = '"C:\Program Files\Pix4Dmapper\pix4dmapper.exe"', stdout = sys.__stdout__ ):
	sys.stdout = stdout
	pixcmd = [pix4dexe, "-c -n", "--template "+template, "--image-dir "+image_dir, proj_name]
	pixcmd = " ".join(pixcmd)
	#print(pixcmd)
	s.call(pixcmd,shell=True)
	
#initial processing
def proc1( proj_name, pix4dexe = '"C:\Program Files\Pix4Dmapper\pix4dmapper.exe"', stdout = sys.__stdout__ ):
	sys.stdout = stdout
	pixcmd = [pix4dexe, "-c -i", proj_name]
	pixcmd = " ".join(pixcmd)
	#print(pixcmd)
	s.call(pixcmd,shell=True)

#steps 2&3	
def proc23( proj_name, pix4dexe = '"C:\Program Files\Pix4Dmapper\pix4dmapper.exe"', stdout = sys.__stdout__ ):
	sys.stdout = stdout
	pixcmd = [pix4dexe, "-c -d -o", proj_name]
	pixcmd = " ".join(pixcmd)
	#print(pixcmd)
	s.call(pixcmd,shell=True)
	
#runs the entire process
def proc( proj_name, pix4dexe = '"C:\Program Files\Pix4Dmapper\pix4dmapper.exe"', stdout = sys.__stdout__ ):
	sys.stdout = stdout
	pixcmd = [pix4dexe, "-c -i -d -o", proj_name]
	pixcmd = " ".join(pixcmd)
	#print(pixcmd)
	s.call(pixcmd,shell=True)
	
def proc_project(proj_name, template, email, password, pix4dexe = '"C:\Program Files\Pix4Dmapper\pix4dmapper.exe"'):
	pixcmd = [pix4dexe, "--email "+email, "--password "+password, "-c --template "+template, "--cam-param-project -i "+proj_name]
	pixcmd = " ".join(pixcmd)
	#print(pixcmd)
	s.call(pixcmd,shell=True)
	
if 	__name__ == "__main__":
	pix4dexe = '"C:\Program Files\Pix4Dmapper\pix4dmapper.exe"'
	email = "stfeirer@ucanr.edu"
	password = "UCANR29049"
	
	tmpl = "C:/Temp/Python/Thermal_Rapid.tmpl"
	#tmpl = "C:/Temp/Python/AG_MS_Rapid.tmpl"
	imgdir = "C:/Temp/Python/MS/1"
	projname = "C:/Temp/Python/MS/1/init.p4d"
	
	create_project(projname, imgdir, email, password, pix4dexe)
	proc_project(projname, tmpl, email, password, pix4dexe)
	
	repname = projname.replace("\\","/").split("/")[-1][:-4]
	report=projname[:-4]+"/1_initial/report/"+repname+"_report.pdf"
	s.Popen(report,shell=True)

#--email stfeirer@ucanr.edu --password UCANR29049 -c --template C:\Temp\Python\Thermal_Rapid.tmpl --cam-param-project -i C:\Temp\Python\Images\init.p4d
#--email stfeirer@ucanr.edu --password UCANR29049 -c -n --image-dir C:\Temp\Python\Images\ C:\Temp\Python\Images\init.p4d