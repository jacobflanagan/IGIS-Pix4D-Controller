import subprocess as s
import glob
import shutil
import os

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '>'):

    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
        print()

#creates a single filename from the original directory structure + orig filename
def dir2file(path):
	return "_".join(path.replace('\\','/').split('/')[1:])
	
def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

#recursively finds files with matching extensions
def find_files(Srcdir, Ext, recursive=True):
	#empty list
	il = []
	for ext in Ext:
		#print(glob.glob(Srcdir+'\\**\\*.'+ext))
		if recursive: il = il+glob.glob(Srcdir+'/**/*.'+ext,recursive=recursive)
		else: il = il+glob.glob(Srcdir+'/*.'+ext,recursive=recursive)
	return il

def copy_drive(Drive, Project, Block, del_src = False):
	imgext = ['img','tif','jpg']
	#get a list of images on the drive
	ifiles = find_files(Drive,imgext)
	
	l=len(ifiles)
	if l<1: return
	i = 0
	printProgressBar(i, l, prefix = 'Copy in Progress:', suffix = 'Complete', length = 50)
	ensure_dir(Project+'/'+Block+"/fake.txt")
	for ifile in ifiles:
		shutil.copy2(ifile, Project+'/'+Block+'/'+Block+"_"+dir2file(ifile))
		if del_src: #remove source file if desired
			os.remove(ifile)
		i = i+1
		printProgressBar(i, l, prefix = 'Copy in Progress:', suffix = 'Complete', length = 50)

def format_drive(Drive, Format, Label):
	cmd = 'format ' + Drive + ' /q /v:' + Label + ' /fs:' + Format
	print(cmd)
	s.call(cmd,shell=True)

if 	__name__ == "__main__":
	#defaults
	drive = 'e:'
	format = "FAT32" #exFAT
	
	copy_drive(drive, "c:/Projects","Card")
	format_drive(drive, format, "IGIS")