import glob, time, os, shutil, errno, sys

import tkinter as tk
from threading import Thread
from threading import Event
from queue import Queue
#downloaded
import dirsync
#own
import pix4d as p4d, subFormat as sf

##Image list - contained in the 

##Processing tags
#process0: 
	#In perm directory: project added, needs to be copied to proc directory (data first, process tag last)
	#In proc directory: project copied, process data through step 1
#process0_pending:
	#In perm directory: likely not finished copying
#process1: 
	#In perm directory: project copied for external processing
	#In proc directory: project processed through step 1
#process1_pending:
	#In proc directory: Waiting for GCP to be completed

#wrapper - output
def text_catcher(text_widget,queue):
	while True:
		t = queue.get().strip('\n').strip('\r')
		#print ("\r" in t)
		
		if t is not "": 
			text_widget.configure(state="normal")
			text_widget.insert(tk.END,  time.strftime("\n%Y-%m-%d %H:%M:%S: ", time.gmtime()), "bold" ) #time.strftime('\n%Y-%m-%d %H:%M:%S GMT', time.gmtime())
			text_widget.insert(tk.END, t)
			text_widget.configure(state="disabled")
			text_widget.see("end")

# Queue that behaves like stdout
class StdoutQueue(Queue):
    def __init__(self,*args,**kwargs):
        Queue.__init__(self,*args,**kwargs)

    def write(self,msg):
        self.put(msg)

    def flush(self):
        sys.__stdout__.flush()

def dictlist2csv(dict_list, filename):
	
	import csv
	
	with open(filename, 'w') as f:
		
		w = csv.DictWriter( f, dict_list[0].keys(), lineterminator='\n' )
		w.writeheader()
		for dict in dict_list:
			w.writerow(dict)
			
	f.close()
			
def csv2dictlist(filename):
	
	import csv
	dict_list = []
	
	with open(filename, 'r') as f:
		
		r = csv.DictReader(f)
		for row in r:
			dict_list.append(row)
			
	f.close()
	return dict_list
		
def get_imagelist(dir):
	
	import hashlib
	
	dir = "\\".join(dirparts(dir))
	il = sf.find_files(dir,["img","jpg","tif"], recursive=False)
	
	d_il = []
	
	for i in il:
		imagename = dirparts(i)[-1]
		checksum = hashlib.md5( open(i,'rb').read() ).hexdigest()
		d_il.append( {"image":imagename, "MD5":checksum} )
	
	return d_il
	
def read_imagelist(ilist_file):
	
	il = {}
	f = open(ilist_file,"r")
	for line in f:
		
		i,cs = line.replace("\n","").split(",")
		
	f.close()
	return il
	
##Compares an image list file with images in the directory; verifies the images, i.e., to ensure all data has been copied
def filelist_differs(dir,imagelist):
	
	il_d = get_imagelist( dir )
	il_f = csv2dictlist( imagelist )
	
	if len(il_d) == len(il_f): #if not the same size, not the same
		
		#lists need to be sorted
		il_d = sorted(il_d, key=lambda k: k['image'])
		il_f = sorted(il_f, key=lambda k: k['image'])
		
		for i in range( 0, len(il_d) ):
			
			if il_d[i] == il_f[i]:
				continue
			else: return True
		
		return False
			
	return True

def log(output):
	
	global app
	
	#print ( time.strftime("%Y-%m-%d %H:%M:%S: ", time.gmtime()) + str(output) )
	app.log(output)

def dirparts(dir):
	return list(filter(None,dir.replace("/","\\").split("\\")))
	
def dircopy(src, dest):
	
	try:
		shutil.copytree(src, dest)
	except OSError as e:
		# If the error was caused because the source wasn't a directory
		if e.errno == errno.ENOTDIR:
			shutil.copy(src, dest)
		else:
			print('Directory not copied. Error: %s' % e)
			
#Copies projects that are ready for initial processing to the processing directory
def copy_project(project, procdir, q):
	
	def log (t):
		q.put(t)
	
	#some params
	initial_il = project+"\\"+"imagelist.process0"
	processing_il = project+"\\"+"imagelist.process1"
	pending_il = project+"\\"+"imagelist.process0_pending"
	
	##SETUP directories
	#ensure proc directory exists
	while not os.path.isdir(procdir):
		print(procdir + " does not, but must exist.")
		input('Fix this, then press enter to continue: ')
	
	#create the pending directory if it doesn't already exist
	if not os.path.isdir(procdir+"\\pending"):
		os.mkdir(procdir+"\\pending")
	##
	
	if os.path.isfile(initial_il):
		
		if filelist_differs(project, initial_il): #if data isn't finished copying
			
			shutil.move( initial_il, pending_il )
			log (project + ": Image list differs from images in directory; may still being copied. Appying pending tag.")
		
		elif dirparts(project)[-1].split("_")[-1] in ["RedEdge","X3","FLIR"]: #verify sensor
			
			dst = procdir+"\\"+dirparts(project)[-1]
			dircopy(project, dst)
			#create a file indicating where this project needs to be synced back to
			with open(dst + "\\srcdir",'w') as f:
				f.write(project)
			log (project + ": Copied to the processing directory.")
			shutil.move(initial_il, processing_il) #change to processing tag
			
		else:
			
			shutil.move(project+"\\"+"imagelist.process0", project+"\\"+"imagelist.unknownsensor")
			log ("Unknown Sensor: " + dirparts(project)[-1])
			
	elif os.path.isfile(pending_il):
		
		if filelist_differs(project, pending_il): #verify all data was copied
			#log ("List still differs; may still being copied.")
			return
		else:
			shutil.move( pending_il, initial_il ) #turn back to inital proc tag (process0)
	
class permdirectory_monitor(Thread):
	
	def __init__(self, dir, procdir, comm_queue, interval=1):
		
		Thread.__init__(self)
		self.exit = Event()
		
		self.dir = "\\".join(dirparts(dir))
		self.procdir = procdir
		self.interval = interval
		
		self.q = comm_queue
		
		#self.persist = True
	
	def run(self):
		
		#while self.persist:
		while not self.exit.is_set():
			
			projects = glob.glob(self.dir+'/**/imagelist.process0*',recursive=True)
			
			#projects = glob.glob( dir+"\\*/") #get project directories
			
			for project in projects:
				
				project = "\\".join( dirparts(project)[0:-1] ) 
				copy_project( project, self.procdir, q )
				
			time.sleep(self.interval)
			
		self.q.put("Monitoring of permanent directory has ceased.")
	
	def shutdown(self):
		
		self.exit.set()
		#self.persist = False
		self.q.put( "Shutting down permanent directory monitor. Please wait until ceased...")

def process_project( project, pendingdir, q ):
	
	def log (t):
		q.put(t)
	
	sensor_dictionary = {"X3":"3DMaps.tmpl", "RedEdge":"AgMultispectral.tmpl", "FLIR":"ThermalCamera.tmpl"}
	
	#some params
	initial_il = project+"\\"+"imagelist.process0"
	processing_il = project+"\\"+"imagelist.process1"
	pending_il = project+"\\"+"imagelist.process0_pending"
	finished_il = project+"\\"+"imagelist.process3"
	
	projectname = dirparts(project)[-1]
	sensor = projectname.split("_")[-1]
	
	if os.path.isfile(initial_il) and not filelist_differs(project, initial_il): #only start if data is finished copying
		
		if sensor in sensor_dictionary:
			
			#create project
			p4d.create(project+"\\"+projectname, os.getcwd()+"\\"+sensor_dictionary[sensor], project )
			#process through step 1
			p4d.proc1( project+"\\"+projectname )
			
			if os.path.isdir( project + "\\GCPs" ): #if the gcp directory exists, copy to pending directory
				
				shutil.move(initial_il, pending_il)
				shutil.move(project, pendingdir+"\\"+projectname )
				
				log(project + ": Moved to Pending")
				
			else: #switch tag to indicate process1
				
				shutil.move(initial_il, processing_il)
				log (project + ": Processed through step 1, tagged for steps 2 & 3.")
			
		else:
			
			#sensor unknown - this is unlikely, as copy checks sensors already
			shutil.move(initial_il, project+"\\"+"imagelist.unknownsensor")
			log ("Unknown Sensor: " + dirparts(project)[-1])
			
	elif os.path.isfile(processing_il): #step 1 finished (and manual GCP/Calibrations if needed), finish steps 2 and 3
		
		log ( project + ": Processing steps 2 & 3." )
		p4d.proc23( project+"\\"+projectname ) #finish steps 2 and 3
		shutil.move(processing_il, finished_il) #tag as finished
		with open(project+"\\srcdir") as f:
			src = f.readline()
		dirsync.sync( project, src, "sync" ) #sync with src directory
		
		#clean up
		os.remove(src+"\\"+"imagelist.process1")
		shutil.rmtree(project, ignore_errors=True)
		
		log ("Finished: " + src)
	
class procdirectory_monitor(Thread):
	def __init__(self, dir, pendingdir, comm_queue, interval=1):
		
		Thread.__init__(self)
		self.exit = Event()
		
		self.dir = "\\".join( dirparts(dir)) 
		self.pendingdir = "\\".join( dirparts(pendingdir) )
		self.interval = interval
		
		self.q = comm_queue
		
	def run(self):
	
		while not self.exit.is_set():
			
			projects = glob.glob(self.dir+'/**/imagelist.process0',recursive=True)
			projects = projects + glob.glob(self.dir+'/**/imagelist.process1',recursive=True)
			
			for project in projects:
				#strip just the project directory (not the image list)
				project = "\\".join(dirparts(project)[0:-1])
				
				process_project( project, self.pendingdir, self.q )
			
			time.sleep(self.interval)
			
		self.q.put("Monitoring of processing directory has ceased.")
		
	def shutdown(self):
		
		self.exit.set()
		self.q.put("Shutting down processing directory monitor. Please wait until ceased...")

class settings(dict):
	
	def __init__(self, file, *args, **kwargs):
		
		super(settings, self).__init__(*args, **kwargs)
		for arg in args:
			if isinstance(arg, dict):
				for k, v in arg.items():
					self[k] = v
					
		if kwargs:
			for k, v in kwargs.items():
				self[k] = v

		import json
		self.file = file
		
		try:
			with open(file, 'r') as f:
				items = json.load(f)
				for k, v in items.items():
					self[k] = v
			f.close()
		except: #start a new file
			self['permdir']=''
			self['procdir']=''
			self['penddir']=''
	
	def write(self):
		
		import json
		
		with open(self.file,'w') as file:
			json.dump(self, file, indent=2)
		file.close()

class GUI(tk.Frame):
	
	def __init__(self, comm_queue, master=None):
		tk.Frame.__init__(self, master)
		self.pack(expand="yes", fill="both")
		
		self.q = comm_queue
		
		self.monstate = True
		self.permdir_monitor = permdirectory_monitor( "","", self.q )
		self.procdir_monitor = procdirectory_monitor( "", "", self.q )
		
		self.createWidgets()
	
	def monitor_switch(self):
		
		if self.monstate:
			
			self.disable()
			self.monstate = False
			
			#Start the monitoring
			self.permdir_monitor = permdirectory_monitor( self.ent1.get(), self.ent2.get(), self.q )
			self.permdir_monitor.start()
			self.procdir_monitor = procdirectory_monitor( self.ent2.get(), self.ent3.get(), self.q )
			self.procdir_monitor.start()
			
			self.q.put("Monitoring initiated.")
			
		else:
			
			#self.log("Monitoring shutting down...")
			self.enable()
			self.monstate = True
			
			self.permdir_monitor.shutdown()
			self.procdir_monitor.shutdown()
			#self.permdir_monitor.join() #will freeze program until these join
			#self.procdir_monitor.join()
			
		
	def disable(self):
		self.ent1.config(state='disabled')
		self.ent2.config(state='disabled')
		self.ent3.config(state='disabled')
		
	def enable(self):
		self.ent1.config(state='normal')
		self.ent2.config(state='normal')
		self.ent3.config(state='normal')
		
	def log(self, t):
		self.output_lbox.configure(state="normal")
		self.output_lbox.insert(tk.END,  time.strftime("\n%Y-%m-%d %H:%M:%S: ", time.gmtime()), "bold" ) #time.strftime('\n%Y-%m-%d %H:%M:%S GMT', time.gmtime())
		self.output_lbox.insert(tk.END, t)
		self.output_lbox.configure(state="disabled")
		self.output_lbox.see("end")

	def createWidgets(self):
		
		global prog_settings
		
		label_pady = 5
		#perm directory Label
		lbl1 = tk.LabelFrame(self, text="Permanent Directory", padx=5, pady=5, height = 65)
		lbl1.pack_propagate(0)
		lbl1.pack(side = tk.TOP, fill="both", expand="no", padx=5, pady=label_pady)
		
		self.ent1 = tk.Entry(lbl1, borderwidth = 5, relief=tk.FLAT)
		self.ent1.insert(tk.END, prog_settings['permdir'] ) #d_settings['project'])
		self.ent1.pack(side = tk.LEFT, fill=tk.X, expand="yes", padx=5, pady=2)
		
		#perm directory Label
		lbl2 = tk.LabelFrame(self, text="Processing Directory", padx=5, pady=5, height = 65)
		lbl2.pack_propagate(0)
		lbl2.pack(side = tk.TOP, fill="both", expand="no", padx=5, pady=label_pady)
		
		self.ent2 = tk.Entry(lbl2, borderwidth = 5, relief=tk.FLAT)
		self.ent2.insert(tk.END, prog_settings['procdir'] ) #d_settings['project'])
		self.ent2.pack(side = tk.LEFT, fill=tk.X, expand="yes", padx=5, pady=2)
		
		#pend directory Label
		lbl3 = tk.LabelFrame(self, text="Processing Directory", padx=5, pady=5, height = 65)
		lbl3.pack_propagate(0)
		lbl3.pack(side = tk.TOP, fill="both", expand="no", padx=5, pady=label_pady)
		
		self.ent3 = tk.Entry(lbl3, borderwidth = 5, relief=tk.FLAT)
		self.ent3.insert(tk.END, prog_settings['penddir'] ) #d_settings['project'])
		self.ent3.pack(side = tk.LEFT, fill=tk.X, expand="yes", padx=5, pady=2)
		
		#btn1 = tk.Button(lbl1, text="Monitor", command=self.say_hi, padx=5, pady=5, borderwidth = 1)
		#btn1.config( height = 1, width = 1)
		#btn1.pack(side = tk.RIGHT, padx=5, pady=5)
		
		self.monitor = tk.Button(self)
		self.monitor["text"] = "Monitor"
		self.monitor["command"] = self.monitor_switch
		self.monitor.pack(side="top", padx=5, pady=5)
		
		#Output Label
		lbl4 = tk.LabelFrame(self, text="Process Output", padx=5, pady=5, height = 300, width = 500)
		lbl4.pack_propagate(0)
		lbl4.pack(side = tk.TOP, fill="both", expand="no", padx=5, pady=label_pady)
		
		self.output_lbox = tk.Text(lbl4, borderwidth = 0, relief=tk.FLAT, state="disabled", font=("Helvetica", 8), width = 60, height = 20) #height=5, 
		self.output_lbox.tag_configure("bold", font="Helvetica 8 bold")
		scrollbar = tk.Scrollbar(lbl4, orient="vertical")
		scrollbar.config(command=self.output_lbox.yview)
		self.output_lbox.config(yscrollcommand=scrollbar.set)
		scrollbar.pack(side=tk.RIGHT, fill="y")
		self.output_lbox.pack(side=tk.LEFT, fill="both", expand=True) #, padx=5, pady=5)
		
		self.output_lbox.configure(state="normal")
		self.output_lbox.insert(tk.END, time.strftime("%Y-%m-%d %H:%M:%S: ", time.gmtime()), "bold" )
		self.output_lbox.insert(tk.END, "Logging using UTM time.")
		self.output_lbox.configure(state="disable")
		
		'''
		self.QUIT = tk.Button(self)
		self.QUIT["text"] = "QUIT"
		self.QUIT["fg"]   = "red"
		self.QUIT["command"] =  self.quit

		self.QUIT.pack({"side": "left"})

		self.hi_there = tk.Button(self)
		self.hi_there["text"] = "Hello",
		self.hi_there["command"] = self.say_hi

		self.hi_there.pack({"side": "left"})
		'''

	def shutdown(self):
		
		global root
		prog_settings
		
		prog_settings['permdir']=self.ent1.get() 
		prog_settings['procdir']=self.ent2.get() 
		prog_settings['penddir']=self.ent3.get() 
		prog_settings.write()
		
		root.destroy()


##communication queue for output
q = StdoutQueue( maxsize=-1 )

##globals
con = True
#load or create settings
prog_settings = settings('settings.json')

#Create GUI
root = tk.Tk()
root.title("IGIS Pix4D Processing")
#root.geometry("400x300")
app = GUI(comm_queue=q, master=root)

# Instantiate and start the text monitor
t_monitor = Thread(target=text_catcher,args=(app.output_lbox, q,))
t_monitor.daemon = True
t_monitor.start()

root.protocol( "WM_DELETE_WINDOW", app.shutdown )
tk.mainloop()
#root.destroy()

sys.exit()

##Perm Directory Monitor
permdir_monitor = Thread( target=permdirectory_monitor, args=("C:/Projects/Test/IGIS_P4DProc/monme","C:/Projects/Test/IGIS_P4DProc/procdir",) )
permdir_monitor.daemon = True
permdir_monitor.start()

##Processing Directory Monitor
procdir_monitor = Thread( target=procdirectory_monitor, args=("C:/Projects/Test/IGIS_P4DProc/procdir","C:/Projects/Test/IGIS_P4DProc/procdir/pending",) )
procdir_monitor.daemon = True
procdir_monitor.start()

while con:
	t = input("Type kill to stop threads: ")
	if t == "kill": con = False
	#print ( "con is: " + str(con) )

permdir_monitor.join()
procdir_monitor.join()

##Monitor
#permdirectory_monitor("C:/Projects/Test/IGIS_P4DProc/monme","C:/Projects/Test/IGIS_P4DProc/procdir")

#process_project( "C:/Projects/Test/IGIS_P4DProc/procdir/2018-10-23_SNARLCemetery0944_M100_X3", "C:\\Projects\\Test\\IGIS_P4DProc\\procdir\\pending" )

#dircopy("C:\\Projects\\Test\\IGIS_P4DProc\\monme\\2018-10-23_SNARLCemetery0944_M100_X3","C:\\Projects\\Test\\IGIS_P4DProc\\procdir"+"\\"+dirparts("C:\\Projects\\Test\\IGIS_P4DProc\\monme\\2018-10-23_SNARLCemetery0944_M100_X3")[-1])

##creating the file
#dictlist2csv(get_imagelist("C:\\Projects\\Test\\IGIS_P4DProc\\monme\\2018-10-23_SNARLCemetery0944_M100_X3"), "C:\\Projects\\Test\\IGIS_P4DProc\\monme\\2018-10-23_SNARLCemetery0944_M100_X3\\imagelist.process0")

##checking difference
#log( filelist_differs("C:\\Projects\\Test\\IGIS_P4DProc\\monme\\2018-10-23_SNARLCemetery0944_M100_X3","C:\\Projects\\Test\\IGIS_P4DProc\\monme\\2018-10-23_SNARLCemetery0944_M100_X3\\imagelist.process0") )

#read_imagelist("C:\\Projects\\Test\\IGIS_P4DProc\\monme\\2018-10-23_SNARLCemetery0944_M100_X3\\imagelist.process0")
#print (filelist_differs("C:\\Projects\\Test\\IGIS_P4DProc\\monme\\2018-10-23_SNARLCemetery0944_M100_X3") )