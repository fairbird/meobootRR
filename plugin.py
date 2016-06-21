from __init__ import _

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Pixmap import Pixmap
from Components.Sources.List import List
from Components.ConfigList import ConfigListScreen
from Components.config import getConfigListEntry, config, ConfigYesNo, ConfigText, ConfigSelection, NoSave
from Plugins.Plugin import PluginDescriptor
from Screens.Standby import TryQuitMainloop
from Screens.MessageBox import MessageBox
from Screens.Console import Console
from Screens.Screen import Screen
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import fileExists, pathExists, createDir
from os import system, listdir, remove as os_remove, popen
from os.path import isdir as os_isdir
from enigma import eTimer

PLUGINVERSION = "2.0"
class MyUpgrade(Screen):
	skin = """
	<screen position="center,center" size="400,200" title="Meoboot">
		<widget name="lab1" position="10,10" size="380,180" font="Regular;24" halign="center" valign="center" transparent="1"/>
	</screen>"""


	def __init__(self, session):
		Screen.__init__(self, session)

		self["lab1"] = Label(_("Meoboot: Upgrading in progress\nPlease wait..."))
		
		self.activityTimer = eTimer()
		self.activityTimer.timeout.get().append(self.updateInfo)
		self.onShow.append(self.startShow)
		
	def startShow(self):
		self.activityTimer.start(10)
		
	def updateInfo(self):
		self.activityTimer.stop()
#		system("touch /boot/dummy")
#		if fileExists("/boot/dummy"):
#			os_remove("/boot/dummy")
		if fileExists("/.meoinfo"):
			self.myClose(_("Sorry, Meoboot can be installed or upgraded only when booted from Flash"))
			self.close()
		else:
			system("chown -R root:root /usr/lib/enigma2/python/Plugins/Extensions/MeoBoot")
			system("chmod -R a+x /usr/lib/enigma2/python/Plugins/Extensions/MeoBoot/contrib")
			system("chmod a+x /usr/lib/enigma2/python/Plugins/Extensions/MeoBoot/ex_init.py")
			for fn in listdir("/media/meoboot/MbootM"):
				dirfile = "/media/meoboot/MbootM/" + fn
         			if os_isdir(dirfile):
					target = dirfile + "/usr/lib/enigma2/python/Plugins/Extensions/MeoBoot"
					cmd = "rm -r " + target + " > /dev/null 2>&1"
					system(cmd)
					cmd = "cp -r /usr/lib/enigma2/python/Plugins/Extensions/MeoBoot " + target
					system(cmd)
					cmd = "cp -r /usr/lib/enigma2/python/Plugins/Extensions/MeoBoot/contrib/meoinit /sbin/meoinit"
					system(cmd)
		
			out = open("/media/meoboot/MbootM/.version", "w")
			out.write(PLUGINVERSION)
			out.close()
			self.myClose(_("MeoBoot successfully updated. You can restart the plugin now.\nHave fun !!"))
		
	def myClose(self, message):
		self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
		self.close()
		

class mbInstallMain(Screen):
	skin = """
	<screen position="center,center" size="700,550" title="Meoboot">
		<widget name="lab1" position="20,10" size="660,180" font="Regular;24" halign="center" valign="center" transparent="1"/>
		<widget name="lab2" position="20,200" size="660,30" font="Regular;22" halign="center" valign="center" transparent="1"/>
		<widget source="list" render="Listbox" position="40,230" zPosition="1" size="620,260" scrollbarMode="showOnDemand" transparent="1" >
			<convert type="StringList" />
		</widget>
		<ePixmap position="45,500" size="140,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MeoBoot/icons/red.png" alphatest="on" zPosition="1" />
        	<ePixmap position="485,500" size="140,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MeoBoot/icons/green.png" alphatest="on" zPosition="1" />
		<widget name="key_red" position="50,500" zPosition="2" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="red" transparent="1" />
		<widget name="key_green" position="490,500" zPosition="2" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="green" transparent="1" />
	</screen>"""


	def __init__(self, session):
		Screen.__init__(self, session)

		self["lab1"] = Label("")
		self["lab2"] = Label(_("Available devices:"))
		
		self["key_red"] = Label(_("Install"))
		self["key_green"] = Label(_("Devices.."))
		self["list"] = List([])
		
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"back": self.close,
			"ok": self.myInstall,
			"red": self.myInstall,
			"green": self.myTools
		})
		self.machine = "vuplus"
		self.activityTimer = eTimer()
		self.activityTimer.timeout.get().append(self.updateInfo)
		self.onShow.append(self.startShow)
		
	def startShow(self):
# Try to mount all devices
		self.activityTimer.start(10)
		
	def updateInfo(self):
		self.activityTimer.stop()
		self.flist = []
		
		f = open("/proc/mounts",'r')
 		for line in f.readlines():
 			if line.find(' /universe') != -1:
 				continue
			elif line.find(' ext') != -1:
				parts = line.strip().split()
				self.flist.append(parts[1])
		f.close()
		self["list"].list = self.flist
		
		message = _("Welcome to MeoBoot installation.\nPlease select a device in the below list and click the red button to install MeoBoot on your preferred device.")
		if len(self.flist) == 0:
			message = _("Welcome to MeoBoot installation.\nSorry it seems that there are not Linux formatted devices mounted on your Vu+. To install MeoBoot you need a Linux formatted part1 device. Click on the green button to format your device.")
		
		self["lab1"].setText(message)
		
		
		if fileExists("/.meoinfo"):
			self.myClose(_("Sorry, Meoboot can be installed or upgraded only when booted from Flash"))
		
		
	def myClose(self, message):
		self.session.open(MessageBox, message, MessageBox.TYPE_INFO)
		self.close()
		
	def myInstall(self):
		device = self["list"].getCurrent()
		if device:
			self.instdevice = device.strip()	
			message = _("Are you sure you want to install MeoBoot in:\n ") + self.instdevice + "?"
			ybox = self.session.openWithCallback(self.domyInstall, MessageBox, message, MessageBox.TYPE_YESNO)
			ybox.setTitle(_("Install Confirmation"))
		
	
	def domyInstall(self, answer):
		mydev = ""
		cmd = "cp " + pluginpath + "/contrib/meoinit /sbin/meoinit"
		system(cmd)
		cmd = "ln -sfn /sbin/meoinit /sbin/init"
		system(cmd)
		system("rm -f /media/meoboot")
		cmd = "ln -sfn " + self.instdevice + " /media/meoboot"
		system(cmd)
		system("mkdir /media/meoboot/MbootM")
		system("mkdir /media/meoboot/MbootUpload")
		out = open("/media/meoboot/MbootM/.meoboot", "w")
		out.write("Flash")
		out.close()
		
		f = open("/proc/mounts",'r')
 		for line in f.readlines():
			if line.find(self.instdevice) != -1:
				parts = line.strip().split()
				mydev = parts[0]
		f.close()
		
		if os_isdir("/usr/lib/enigma2/python/Blackhole") == False:
			if mydev:
				out = open("/etc/fstab", "a")		
				line = "\nmount " + mydev + " " + self.instdevice
				out.write(line)
				out.close()
#Upgrade images		
		for fn in listdir("/media/meoboot/MbootM"):
			dirfile = "/media/meoboot/MbootM/" + fn
         		if os_isdir(dirfile):
				target = dirfile + "/usr/lib/enigma2/python/Plugins/Extensions/MeoBoot"
				cmd = "rm -r " + target + " > /dev/null 2>&1"
				system(cmd)
				cmd = "cp -r /usr/lib/enigma2/python/Plugins/Extensions/MeoBoot " + target
				system(cmd)
		
		out = open("/media/meoboot/MbootM/.version", "w")
		out.write(PLUGINVERSION)
		out.close()
		
		self.myClose(_("MeoBoot successfully installed. You can restart the plugin now.\nHave fun !!"))
		
	def myTools(self):
		self.myClose(_("Please, use Black Hole Extra Settings Device Panel to format and map your devices."))


		
class Mystart(Screen):
	skin = """
	<screen position="center,center" size="700,550" title="Meoboot">
		<widget name="lab1" position="20,10" size="660,50" font="Regular;24" halign="center" valign="center" transparent="1"/>
		<widget name="lab2" position="20,60" size="660,30" font="Regular;22" halign="center" valign="center" transparent="1"/>
		<widget name="lab3" position="310,90" size="80,80" transparent="1"/>
		<widget name="lab4" position="20,170" size="660,30" font="Regular;24" halign="center" valign="center" transparent="1"/>
		<widget name="lab5" position="20,200" size="660,30" font="Regular;22" halign="center" valign="center" transparent="1"/>
		<widget source="list" render="Listbox" position="40,230" zPosition="1" size="620,260" scrollbarMode="showOnDemand" transparent="1" >
			<convert type="StringList" />
		</widget>
		<ePixmap position="28,500" size="140,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MeoBoot/icons/red.png" alphatest="on" zPosition="1" />
        	<ePixmap position="196,500" size="140,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MeoBoot/icons/green.png" alphatest="on" zPosition="1" />
		<ePixmap position="364,500" size="140,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MeoBoot/icons/yellow.png" alphatest="on" zPosition="1"/>
		<ePixmap position="532,500" size="140,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MeoBoot/icons/blue.png" alphatest="on" zPosition="1" />
		<widget name="key_red" position="28,500" zPosition="2" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="red" transparent="1" />
		<widget name="key_green" position="196,500" zPosition="2" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="green" transparent="1" />
		<widget name="key_yellow" position="364,500" zPosition="2" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="yellow" transparent="1"/>
		<widget name="key_blue" position="532,500" zPosition="2" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="blue" transparent="1"/>
	</screen>"""


	def __init__(self, session):
		Screen.__init__(self, session)

		self["lab1"] = Label("")
		self["lab2"] = Label("")
		self["lab3"] = Pixmap()
		self["lab4"] = Label("")
		self["lab5"] = Label(_("Available Images"))
		self["key_red"] = Label(_("Install Image"))
		self["key_green"] = Label(_("Boot Image"))
		self["key_yellow"] = Label(_("Delete Image"))
		self["key_blue"] = Label(_("Help"))
		self["list"] = List([])
		
		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"back": self.close,
			"ok": self.bootImage,
			"red": self.extractImage,
			"green": self.bootImage,
			"yellow": self.delImage,
			"blue": self.mytools
		})
		self.availablespace = 0
		self.curimage = ""
		self.onShow.append(self.updateInfo)
		
	def updateInfo(self):
		curimage = "Flash"
		if fileExists("/.meoinfo"):
			f = open("/.meoinfo",'r')
			curimage = f.readline().strip()
			f.close()
		strview = _("Current Running Image: ") + curimage
		self.curimage = curimage
		self["lab1"].setText(strview)
		
		device = "meoboot"
		for d in listdir("/media/"):
			if d == "meoboot":
				continue
			test = "/media/" + d + "/MbootM/.meoboot"
			if fileExists(test):
				device = d
		
		strview = _("MeoBoot Installed on: ") + device
		self["lab2"].setText(strview)
		
		icon = "dev_usb.png"
		if device == "card" or device == "sd":
			icon = "dev_sd.png"
		elif device == "hdd":
			icon = "dev_hdd.png"
		elif device == "cf":
			icon = "dev_cf.png"
	
		icon = pluginpath + "/icons/" + icon
		png = LoadPixmap(icon)
		self["lab3"].instance.setPixmap(png)
		
		device = "/media/" + device
		ustot = usfree = usperc = ""
		rc = system("df > /tmp/ninfo.tmp")	
		
		if fileExists("/tmp/ninfo.tmp"):
			f = open("/tmp/ninfo.tmp",'r')
 			for line in f.readlines():
				line = line.replace('part1', ' ')
				parts = line.strip().split()
				totsp = (len(parts) -1)
				if parts[totsp] == device:
					if totsp == 5:
						ustot = parts[1]
						usfree = parts[3]
						usperc = parts[4]
					else:
						ustot = "N/A   "
						usfree = parts[2]
						usperc = parts[3]
					break
					
			f.close()
			os_remove("/tmp/ninfo.tmp")
		self.availablespace = usfree[0:-3]
		strview =_("Used: ") + usperc + _("   Available: ") + usfree[0:-3] + " MB"
		self["lab4"].setText(strview)
		
		
		imageslist = ["Flash"]
		for fn in listdir("/media/meoboot/MbootM"):
			dirfile = "/media/meoboot/MbootM/" + fn
         		if os_isdir(dirfile):
				imageslist.append(fn)
		
		self["list"].list = imageslist
		
	def mytools(self):
		self.session.open(MyHelp)
		
	def delImage(self):
		image = self["list"].getCurrent()
		if image:
			self.delimage = image.strip()
			myerror = ""
			if self.delimage == "Flash":
				myerror = _("Sorry you cannot delete Flash image")
			if self.delimage == self.curimage:
				myerror = _("Sorry you cannot delete the image currently booted from.")
				
			if myerror == "":
				message = _("Are you sure you want to delete Image:\n ") + image + "?"
				ybox = self.session.openWithCallback(self.dodelImage, MessageBox, message, MessageBox.TYPE_YESNO)
				ybox.setTitle(_("Delete Confirmation"))
			else:
				self.session.open(MessageBox, myerror, MessageBox.TYPE_INFO)
			
		
	def dodelImage(self, answer):
		if answer is True:
			cmd = "echo -e '\n\nMeoboot deleting image..... '"
			cmd1 = "rm -r /media/meoboot/MbootM/" + self.delimage
			#rc = system(cmd)
			self.session.open(Console, _("Meoboot: Deleting Image"), [cmd, cmd1])
			#self.session.open(MessageBox, "Image deleted.", MessageBox.TYPE_INFO)
			self.updateInfo()
		
	def bootImage(self):
		newimage = self["list"].getCurrent()
		if newimage:
			self.rebootimage = newimage.strip()
			message = _("Are you sure you want to Boot Image:\n ") + newimage + "?"
			ybox = self.session.openWithCallback(self.restDream, MessageBox, message, MessageBox.TYPE_YESNO)
			ybox.setTitle(_("Reboot Confirmation"))
		
	
	def restDream(self, answer):
		if answer is True:
			newimage = self["list"].getCurrent()
			if newimage:
				out = open("/media/meoboot/MbootM/.meoboot", "w")
				out.write(self.rebootimage)
				out.close()
				self.session.open(TryQuitMainloop, 2)
				self.close()
			

	def extractImage(self):
		count = 0
		for fn in listdir("/media/meoboot/MbootM"):
			dirfile = "/media/meoboot/MbootM/" + fn
         		if os_isdir(dirfile):
				count = count +1;
		if count > 7:
			myerror = _("Sorry you can install a max of 8 images.")
			self.session.open(MessageBox, myerror, MessageBox.TYPE_INFO)
		elif int(self.availablespace) < 500:
			myerror = _("Sorry there is not enought available space on your device. You need at least 500 Mb free to install a new image")
			self.session.open(MessageBox, myerror, MessageBox.TYPE_INFO)
		else:
			self.session.open(mbImageSetup)
			

class mbImageSetup(Screen, ConfigListScreen):
	skin = """
	<screen position="center,center" size="602,340" title="MeoBoot Image Install">
		<widget name="config" position="10,20" size="580,230" scrollbarMode="showOnDemand" />
		<ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MeoBoot/icons/red.png" position="235,290" size="140,40" alphatest="on" />
		<widget name="key_red" position="235,290" zPosition="1" size="140,40" font="Regular;20" halign="center" valign="center" backgroundColor="#9f1313" transparent="1" />
	</screen>"""
	
	def __init__(self, session):
		Screen.__init__(self, session)
		
		self.list = []
		ConfigListScreen.__init__(self, self.list, on_change = self.schanged)
		self["key_red"] = Label(_("Install"))

		self["actions"] = ActionMap(["WizardActions", "ColorActions"],
		{
			"red": self.imageInstall,
			"back": self.close

		})
		
		fn = "NewImage"
		sourcelist = []
		for fn in listdir("/media/meoboot/MbootUpload"):
         		if fn.find('.zip') != -1:
				fn = fn.replace('.zip', '')
				sourcelist.append((fn,fn))
				
		if len(sourcelist) == 0:
			sourcelist = [("None", "None")]
		self.source = NoSave(ConfigSelection(choices = sourcelist))
		self.target = NoSave(ConfigText(fixed_size = False))
		self.sett = NoSave(ConfigYesNo(default=True))
		
		self.target.value = ""
		self.curselimage = ""
		
		res = getConfigListEntry(_("Source Image file"), self.source)
		self.list.append(res)
		res = getConfigListEntry(_("Image Name"), self.target)
		self.list.append(res)
		res = getConfigListEntry(_("Copy Settings to the new Image"), self.sett)
		self.list.append(res)
		
			
			
			
	def schanged(self):
		if self.curselimage != self.source.value:
			self.target.value = self.source.value
			self.curselimage = self.source.value
			
	def imageInstall(self):
		myerror = ""
		source = self.source.value.replace(' ', '')
		target = self.target.value.replace(' ', '')
		
		for fn in listdir("/media/meoboot/MbootM"):
         		if fn == target:
				myerror = _("Sorry, an Image with the name ") + target + _(" is already installed.\n Please try another name.")
		
		if source == "None":
			myerror = _("You have to select one Image to install.\nPlease, upload your zip file in the folder: /media/meoboot/MbootUpload and select the image to install.")
		if target == "":
			myerror = _("You have to provide a name for the new Image.")
		if target == "Flash":
			myerror = _("Sorry this name is reserved. Choose another name for the new Image.")
		
		if len(target) > 35:
			myerror = _("Sorry the name of the new Image is too long.")
		
		if(myerror):
			self.session.open(MessageBox, myerror, MessageBox.TYPE_INFO)
		else:
			message = "echo -e '\n\n"
			message += _("Meoboot will stop all your openView activity now to install the new image.")
			message += _("Your openView will freeze during the installation process.")
			message += _("Please: DO NOT reboot your openView and turn off the power.\n")
			message += _("The new image will be installed and auto booted in few minutes.")
			message += "'"
			cmd1 = pluginpath + "/ex_init.py"
            		cmd = "%s %s %s %s" % (cmd1, source, target, str(self.sett.value))
            		self.session.open(Console, _("Meoboot: Install new image"), [message, cmd])
	

class MyHelp(Screen):
	skin = """
	<screen position="center,center" size="700,550" title="Meoboot Help">
		<widget name="lab1" position="20,20" size="660,510" font="Regular;20" />
	</screen>"""


	def __init__(self, session):
		Screen.__init__(self, session)

		self["lab1"] = ScrollLabel("")
		self["actions"] = ActionMap(["WizardActions", "ColorActions", "DirectionActions"],
		{
			"back": self.close,
			"ok": self.close,
			"up": self["lab1"].pageUp,
			"left": self["lab1"].pageUp,
			"down": self["lab1"].pageDown,
			"right": self["lab1"].pageDown,
		})
		self["lab1"].hide()
		self.updatetext()
		
	def updatetext(self):
		message = "MEOBOOT V." + PLUGINVERSION + " for openView \nLight Multiboot\n\n"
		message += "Author: Bacicciosat aka *meo \nGraphics: Army\nMain tester: matrix10\n\n"
		message += _("Requirements:\nMeoBoot require a openView machine and Hdd or Usb pen drive.\n\n")
		message += _("Instructions:\nMeoBoot installation and upgrade is easy and intuitive.\nTo install a new image in multiboot you have only to upload your *.zip file in the folder \"/media/meoboot/MbootUpload\" and click on the <Install Image> button>\n\n")
		message += _("Uninstall Meoboot:\nTo completely remove meoboot form your flash image you have to delete the folders:\n/media/meoboot/MbootM\n/media/meoboot/MbootUpload\n/media/meoboot\n/usr/lib/enigma2/python/Plugins/Extensions/MeoBoot\n\n")
		message += _("Have fun !!")
		self["lab1"].show()
		self["lab1"].setText(message)
	
	

def main(session, **kwargs):
		version = 0
		if fileExists("/media/meoboot/MbootM/.version"):
			f = open("/media/meoboot/MbootM/.version")
    			version = float(f.read())
			f.close()
		if fileExists("/media/meoboot/MbootM/.meoboot"):
			if float(PLUGINVERSION) > version:
				session.open(MyUpgrade)
			else:
				session.open(Mystart)
		else:
			session.open(mbInstallMain)


def Plugins(path,**kwargs):
	global pluginpath
	pluginpath = path
	return PluginDescriptor(name="MeoBoot", description=_("E2 Light Multiboot"), icon="plugin_icon.png", where = PluginDescriptor.WHERE_PLUGINMENU, fnc=main)
