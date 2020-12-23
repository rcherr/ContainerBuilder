from tkinter import *
from tkinter import ttk, font, messagebox, filedialog
from PIL import Image, ImageTk
import os, math

# Globals
DPI = 96

class MainFrame(Frame):

	# Variable Declaration
	# Variables about the Image that is being Dragged.
	dragging=False
	dragging_units = 1
	dragging_fname=None
	dragging_image=None
	dragging_image_tracker=-1
	# TKinter widgets
	canvas=None
	combobox_definition=None
	combobox_scale=None
	treeview_node_root = None
	treeview_main = None
	# Tracking some attributes of the current Rack.
	rack_unit_1u_height = 0
	rack_unit_1u_width = 0
	rack_sample_wall_width = 0
	rack_sample_lip_height_top = 0
	rack_sample_lip_height_bot = 0
	selected_rack_unit=None
	# Canvas Tracking
	bboxes = []
	runits = []
	rectangles = []
	mouse_x=0
	mouse_y=0
	canvas_width = 0
	canvas_height = 0
	# Image Tracking
	image_scale = 1
	canvas_scale = 1
	# Images
	current_container_image=None
	current_container_photo=None
	current_container_tracker=-1
	# MAPS
	definition_map={}
	dragging_image_unit_map={}
	image_map_resized={}
	rack_unit_arr={}
	image_map={}
	original_image_map={}
	#
	current_definition_file=None
	# Paths to our internal files
	dir_path_img = os.path.join(os.getcwd(), "img")
	dir_path_input = os.path.join(os.getcwd(), "input")
	dir_path_output = os.path.join(os.getcwd(), "output")
	# End of Variable Declaration
		
	def __init__(self, master):
		
		#
		Frame.__init__(self, master)
		self.master = master
 
		# Defining the initial dimensions for the Frame and inside containers
		# Most of these can be deleted in future versions.
		display_wth = self.winfo_screenwidth()
		display_hgt = self.winfo_screenheight()
		frame_wth = (display_wth // 2) - 128
		frame_hgt = display_hgt // 2
		frame_wth_info = frame_wth
		frame_hgt_info = 8
		frame_wth_image = frame_wth * .3 #96			 
		frame_hgt_image = frame_hgt - frame_hgt_info
		self.canvas_width = frame_wth - frame_wth_image
		self.canvas_height = frame_hgt - frame_hgt_info

		# Define some fonts for styling
		treeview_font = font.Font(family="Helvetica", size=7, weight="normal")
		treeview_heading_font = font.Font(family="Helvetica", size=8, weight="normal")

		# Define the style for the different widgets
		treeview_style = ttk.Style()
		treeview_style.configure("Treeview", font=treeview_font)
		treeview_heading_style = ttk.Style()
		treeview_heading_style.configure("Treeview.Heading", font=treeview_font)

		# Setup the dimensions for the Frame
		self.master.geometry(f"{frame_wth}x{frame_hgt}+{(display_wth//2-frame_wth//2)}+{(display_hgt//2-frame_hgt//2)}")
		self.config(width = frame_wth, height = frame_hgt)
		self.master.title("Container Builder")

		# Create the Frame that will host all of the information about what is going on the screen
		frame_info = Frame(self,  bd = 1, relief = RAISED)
		#label_mouse = Label(frame_info, text="TEST")
		button_save = Button(frame_info, command=self.export_image, text="Save") # Replace with icon soon.
		button_save.pack(side=LEFT)
		button_open = Button(frame_info, text="Open")
		button_open.pack(side=LEFT)
		button_frame = Button(frame_info, text="Frame")
		combobox_frame = ttk.Combobox(frame_info)
		combobox_frame.pack(side=LEFT)
		button_switch = Button(frame_info, text="Switch")
		button_switch.pack(side=LEFT)
		combobox_switch = ttk.Combobox(frame_info)
		combobox_switch.pack(side=LEFT)
		button_server = Button(frame_info, text="Server")
		button_server.pack(side=LEFT)
		combobox_server = ttk.Combobox(frame_info)
		combobox_server.pack(side=LEFT)
		label_hostname = Label(frame_info, text="Hostname")
		label_hostname.pack(side=LEFT)
		entry_hostname = Entry(frame_info, textvariable=StringVar())
		entry_hostname.pack(side=RIGHT)
		frame_info.pack(fill=X)
		
		# Create the Frame on the left side of the screen that will handle the loaded files and allow for dragging and dropping. 
		frame_image = Frame(self, bd = 1, relief=RAISED)							
		self.treeview_main = ttk.Treeview(frame_image, height = frame_hgt_image)
		self.treeview_main['columns']=("RU")
		self.treeview_main.column("RU", width = treeview_font.measure("Units") + 4)
		self.treeview_main.heading("RU", text = "Units")
		self.treeview_main.pack()
		frame_image.pack(side = LEFT)

		# [Temp] This is for the space being used by the Canvas on the frame.
		#cnvs_wth = frame_wth - frame_image.cget('width') - treeview_font.measure("*" * 32)
		
		# Define the root node
		self.treeview_node_root = self.treeview_main.insert('','end', text=f"{os.getcwd()}", tags=('touch'))
		
		# Bind the button press event to track dragging
		self.treeview_main.tag_bind('touch', '<Button-1>', self._tracking_enable)

		# Make the Canvas after all that
		frame_canvas = Frame(self, bd = 1, relief = RAISED)
		self.canvas = Canvas(frame_canvas, width = self.canvas_width-2, height = self.canvas_height-2)
		self.canvas.pack()
		frame_canvas.pack(side=LEFT, fill=X)

		# We will keep a map of Container to Container Definition Files and display the
		# Cooresponding CDF file as a label
		#label_cdf = Label(frame_info, text="Definition File")
		#label_cdf.pack(side=LEFT)
		
		# The Combobox that will hold the available scale options
		self.combobox_scale = ttk.Combobox(frame_info)
		#self.combobox_scale.pack(side=RIGHT, anchor='e')
		
		# The Combobox that holds the Container Definition Files.
		self.combobox_definition = ttk.Combobox(frame_info)
		#self.combobox_definition.pack(side=LEFT, anchor = 'w')
		
		# [Button Bindings]
		self.canvas.bind("<Button-1>", self._add_rack_unit)
		self.canvas.bind("<Button-3>", self._remove_rack_unit)
		self.canvas.bind("<Motion>", self.motion)
		
		# Attempt to import the network images
		self.import_images(self.dir_path_img)
	
		# Import the defintion files and set the auto-selected to the last imported.
		# Once we have that we are good to create a frame image. Without it we cannot proceed.
		self.import_definitions(self.dir_path_input)
		
		# Add the values to the combobox
		self.combobox_scale['values'] = ['33%', '66%', '100%', '133%', '150%', '250%', '300%', '400%']
		self.combobox_scale.current(2)
		self.combobox_scale.bind("<<ComboboxSelected>>", self.__change_scale)
		
		# Add those definitions to the Combo Box
		self.combobox_definition['values'] = list(self.definition_map.keys())
		self.combobox_definition.current(0)
		self.combobox_definition.bind("<<ComboboxSelected>>", self._change_container_image)

		# Pack and start
		self.pack(fill = BOTH)
		self.master.resizable(False, False)
		self.mainloop()
		
	def _change_container_image(self, event):
	
		# Delete the old from the canvas if it exists
		if self.current_container_tracker > -1:
			self.canvas.delete(self.current_container_tracker)
			
		# Get the current value of the combobox as the current_definition_file
		self.current_definition_file = self.combobox_definition.get()
		
		# Creation of the RED Rack Units as well as the definition of what self.rack_unit_1u_height will be for rest of program.
		self._create_container_image(self.definition_map[self.current_definition_file], self.dir_path_input)		
		
		# Once we have the frame resized we should also have a definite 1U height set to use to resize the images.
		self._create_resized_images()

	def _create_container_image(self, arr_defs, dir_image):
	
		# Attempt to find that image or bail out
		# Add all the acceptable images types in array
		exts = ['png', 'jpg', 'jpeg']
		found = False
		
		# Now try and find the image
		for root, subdir, files in os.walk(dir_image):
			print(f"Files: {files}")
			if arr_defs[1] in files:
				found = True
				break
			
		# Didn't find the image so kick out.
		if not found:
			return
	
		# Each Rack unit will have multiple images and files associated.
		for i in range(arr_defs[2]):
			self.rack_unit_arr[i] = (None,-1, None)

		# The difference between the workspace and the contaner is that the workspace is the area used only for the
		# Rack Units and the Container describes the Real Life IDF or other Container for the Rack units
		cntr_wth_wall = arr_defs[7] * DPI
		cntr_hgt_lip_bot = arr_defs[6] * DPI
		cntr_hgt_lip_top = arr_defs[5] * DPI
		cntr_wth = arr_defs[4] * DPI
		cntr_hgt = arr_defs[3] * DPI
		
		# Define the workspace by removing the wall width and the top and bottom lips
		work_wth = cntr_wth - (cntr_wth_wall * 2)
		work_hgt = cntr_hgt - (cntr_hgt_lip_top + cntr_hgt_lip_bot)

		# Cut off any extra trim and get each variable down to a multiple of 10.
		work_wth = work_wth - (work_wth % 10)
		work_hgt = work_hgt - (work_hgt % 10)
		cntr_wth_wall = cntr_wth_wall - (cntr_wth_wall % 10)
		cntr_hgt_lip_top = cntr_hgt_lip_top - (cntr_hgt_lip_top % 10)
		cntr_hgt_lip_bot = cntr_hgt_lip_bot - (cntr_hgt_lip_bot % 10)
		cntr_wth = (cntr_wth - (cntr_wth % 10))
		cntr_hgt = (cntr_hgt - (cntr_hgt % 10))

		# Scaling Variables
		scale_counter = 0
		w_temp = cntr_wth
		h_temp = cntr_hgt
		scale_factor = (cntr_wth / cntr_hgt) + .4
		print("Scale Factor: {}".format(scale_factor))
		
		# Now we need to scale that up or down based on the canvas size
		if w_temp >= h_temp:
			if w_temp > self.canvas_width:
				while w_temp > self.canvas_width:
					w_temp = w_temp * scale_factor
					scale_counter = scale_counter + 1
		else:
			if h_temp > self.canvas_height:
				while h_temp > self.canvas_height:
					h_temp = h_temp * scale_factor
					scale_counter = scale_counter + 1
		
		# Scale the workspace and the container down to fit the canvas.
		for i in range(scale_counter):
			work_wth = work_wth * scale_factor
			work_hgt = work_hgt * scale_factor
			cntr_wth_wall = cntr_wth_wall * scale_factor
			cntr_hgt_lip_top = cntr_hgt_lip_top * scale_factor
			cntr_hgt_lip_bot = cntr_hgt_lip_bot * scale_factor
			cntr_wth = cntr_wth * scale_factor
			cntr_hgt = cntr_hgt * scale_factor
		
		# Slap those values up.
		work_wth = math.ceil(work_wth)
		work_hgt = math.ceil(work_hgt)
		cntr_wth_wall = math.ceil(cntr_wth_wall)
		cntr_hgt_lip_top = math.ceil(cntr_hgt_lip_top)
		cntr_hgt_lip_bot = math.ceil(cntr_hgt_lip_bot)
		cntr_wth = math.ceil(cntr_wth)
		cntr_hgt = math.ceil(cntr_hgt)

		# When describing the Rack Units always use the workspace for reference dimensions
		self.rack_sample_lip_height_top = cntr_hgt_lip_top
		self.rack_sample_lip_height_bot = cntr_hgt_lip_bot
		self.rack_unit_1u_width = work_wth
		
		# Let's plot out some locations for the rectangles
		cntr_stx = (self.canvas_width // 2) + (cntr_wth // 2)
		cntr_sty = (self.canvas_height // 2) - (cntr_hgt // 2)
		work_stx = cntr_stx - (cntr_wth // 2)
		work_sty = ((self.canvas_height - cntr_hgt) // 2) + cntr_hgt_lip_top
		
		# Determine the size of 1 Rack Unit. If its not an integer then round it up and adjust the work and container height to fit.
		self.rack_unit_1u_height = math.ceil(work_hgt / arr_defs[2])
		work_hgt = self.rack_unit_1u_height * arr_defs[2]
		cntr_hgt = work_hgt + self.rack_sample_lip_height_top + self.rack_sample_lip_height_bot
					
		# This is a one-liner for opening the image, then resizing it and we keep the reference for the PhotoImage
		# So that it does not get Garbage Collected.
		self.current_container_image = Image.open(os.path.join(self.dir_path_input, arr_defs[1])).resize((int(cntr_wth), int(cntr_hgt)), Image.ANTIALIAS)
		self.current_container_photo = ImageTk.PhotoImage(self.current_container_image)
		
		# Create the image in the center of the canvas for the resized container.
		self.current_container_tracker = self.canvas.create_image(cntr_stx - (cntr_wth // 2), cntr_sty + (cntr_hgt // 2), image = self.current_container_photo)

		font_size = 8
		# Depending on the number of Rack Units possible for this Frame.
		for iter in range(arr_defs[2]):

			# Define the boundaries for the BBOX.
			x = work_stx - (work_wth // 2)
			y = (work_sty) + (iter * self.rack_unit_1u_height)
			wth = work_stx + (work_wth // 2)
			hgt = (work_sty) + ((iter * self.rack_unit_1u_height) + self.rack_unit_1u_height)

			# Define the BBOX
			box = (x, y, wth, hgt)
			
			# We need these rectangles for drawing.
			rectangle = self.canvas.create_rectangle(box[0],box[1],box[2],box[3], fill = "red")
			
			# Draw the Rack Unit next to that.
			runit = self.canvas.create_text(box[0] - font_size * 3, box[1] + font_size // 2, fill="black", font="LucidaConsole {} bold".format(font_size), text="{}-".format(42 - iter))

			# We need the bboxes for mouse entry detection.
			self.bboxes.append(box)
			self.runits.append(runit)
			self.rectangles.append(rectangle)
		
		# Important Measurement here. This describes our programs usable rack wall width which will determine our
		# positioning during the export of the image
		self.rack_sample_wall_width = (cntr_wth - work_wth) // 2
	
	def _create_resized_images(self):
	
		# Clear it out
		if len(self.treeview_main.get_children()) > 0:
			self.treeview_main.delete(*self.treeview_main.get_children())
			self.treeview_node_root = self.treeview_main.insert('','end', text=f"{os.getcwd()}", tags=('touch'))

		# In a future revision each image will need a config file with it to determine the number of rack units to use
		for k, v in self.image_map.items():
			
			# Parse the Number of Rack units from the name
			units = 1
			
			# Just skip if ill-formated.
			try:

				# Grab the number of Rack Units from file name; ignore files without this format
				units = int(os.path.basename(k).split("_")[0])
				
				# Why this dictionary? This keeps a track of how many RUs each file takes up.
				self.dragging_image_unit_map[k] = units
			except ValueError:
				print("Failed to parse")
				continue
				
			# Open the Image up and resize it to the size of a 1U Rack * How many units it thinks it is.
			#img = Image.open(k)
			img = v[0].resize((int(self.rack_unit_1u_width), int(math.ceil(self.rack_unit_1u_height * units))), Image.ANTIALIAS)

			# Not advised, but I re-assigned a tuple to a new tuple with a new size.			
			tup = self.image_map[k]

			# TESTING, if this works then get rid of image_map_resized
			self.image_map[k] = (tup[0], tup[1], img)
			self.image_map_resized[k] = ImageTk.PhotoImage(img)
			self.treeview_main.insert(self.treeview_node_root, 'end', text=os.path.basename(k), values=(f"{units}"), tags=('touch'))

	def _remove_rack_unit(self, event):

		# Regardless clear the previous used information
		self.dragging = False
		self.dragging_image = None
		if self.dragging_image_tracker > -1: self.canvas.delete(self.dragging_image_tracker)
		self.dragging_image_tracker = -1
		self.dragging_fname = None

		# Get the Bounding Box at the click location
		bbox = self._get_bbox_at_position(event.x, event.y)

		# No bbox then stop.
		if bbox == None:
			return

		# Find what's at this location
		item = self.canvas.find_overlapping(bbox[0],bbox[1],bbox[2],bbox[3])
		
		# Do some list comprehension to get rid of the rectangles and the container image.
		item = [i for i in item if i not in self.rectangles and not i == self.current_container_tracker]
		
		# Not hovering over anything? Stop.
		if item == None:
			return
		
		# Delete them straight up.
		for i in item:
			self.canvas.delete(i)
			
		# Remove those entries from the rack unit array
		for k, v in self.rack_unit_arr.items():
			if v[1] in item:
				self.rack_unit_arr[k] = (None, -1, None)

	def _add_rack_unit(self, event):
		
		# If you're not holding an image then kick out
		if self.dragging_image == None or self.dragging_image_tracker == -1:
			return

		# Find out what we're hovering over
		bbox = self._get_bbox_at_position(event.x, event.y)
		
		# Clear the hover image if you're not hovering over a bbox.
		if bbox == None:
			self.canvas.delete(self.dragging_image_tracker)
			self.dragging_image_tracker = None
			self.dragging_image = None
			self.dragging = False
			return

		bbox_index = self.bboxes.index(bbox)

		for iter in self.rack_unit_arr.values():
			if bbox_index in iter:
				return
		
		# Is there something at the current rack unit then stop.
		#if not self.rack_unit_arr[bbox_index] == None:
		#		return
		
		# Define the offset between each bbox
		offset = self.rack_unit_1u_height * self.dragging_units

		# Relate the image that your dropping with the rack unit you're over
		# This array is tracking the File Name of the image we're dragging, the canvas image tracker, the image, and the position
		self.rack_unit_arr[bbox_index] = (self.dragging_fname, self.dragging_image_tracker, self.dragging_image)		
		
		# Snap the image to the location of the bbox
		self.canvas.coords(self.dragging_image_tracker, ((bbox[0] + bbox[2]) //2,  bbox[1] + (offset // 2)))
			
		# [Delete the Below if you want to have to select another Item after each add.]
		# Stop Dragging the Image, Clear the reference to the dragging image when uncommented.
		#self.dragging = False
		#self.dragging_fname = None
		#self.dragging_image = None
		self.dragging_image_tracker=self.canvas.create_image((self.mouse_x, self.mouse_y), image=self.dragging_image)

	def _tracking_enable(self, event):
		
		# Start tracking and remove the previous image
		self.canvas.delete(self.dragging_image_tracker)

		# Find what was selected
		selected_item = self.treeview_main.identify('item', event.x, event.y)

		# Kick out if there's not a valid selection.
		if selected_item == '':
			return

		# Grab the actual
		selected_node = self.treeview_main.item(selected_item)
		
		# No node then stop.
		if selected_node == None:
			return

		# FName
		fname = ""

		# The text is actually just the base name of what is in the image_map_resized
		for k, v in self.image_map_resized.items():
			if selected_node['text'] == os.path.basename(k):
				fname = k

		# The name of the image must exist in the resized image map.
		if not fname == "":

			# Grab the text
			self.dragging_image = self.image_map_resized[fname]

			# No image associated with the name of the that image? Stop.
			if self.dragging_image == None:
				return

			# Add that to the canvas
			self.dragging = True
			self.dragging_fname = fname
			self.dragging_image_tracker = self.canvas.create_image(self.mouse_x, self.mouse_y, image = self.dragging_image)
			self.dragging_units = int(self.dragging_image_unit_map[fname])
		
	def import_definitions(self, dir):
	
		# Acceptable file types is just cdf, but maybe later I'll accept text files
		exts = [".cdf"]
		
		#
		for fil in os.listdir(dir):
			
			# File
			fil = os.path.join(os.path.abspath(dir), fil)
			
			# Yeah, we're only taking files.
			if os.path.isfile(fil):
			
				# Grab the extension for the file given
				ext = os.path.splitext(fil)[1]
				
				#
				if ext in exts:
					
					# Read the file
					values = self.read_container_def_file(fil)
				
					# Check the length
					if not -1 in values:
					
						#
						self.definition_map[os.path.basename(fil)] = values
				
						# Always set to the last successfully imported cdf file.
						self.current_definition_file = os.path.basename(fil)

	def import_images(self, dir):

		# Acceptable images types
		image_types = ['.png', '.jpeg', '.bmp', '.jpg']

		#
		for fil in os.listdir(dir):
			
			# 
			fil = os.path.join(os.path.abspath(dir), fil)
			
			# Only process files; if I wasn't lazy I would make this recursive so we can use sub-directories.
			if os.path.isfile(fil):

				# Grab the extension
				ext = os.path.splitext(fil)[1]
				
				# Yeah that image type is supported
				if ext in image_types:
					
					# PIL Image
					image_pil = Image.open(fil)

					# ImageTk PhotoImage
					image_tk = ImageTk.PhotoImage(image_pil)

					# Map the name of the image to a normal PIL.Image, ImageTk.PhotoImage, [resized] ImageTk.PhotoImage?
					self.image_map[fil] = (image_pil, image_tk)
		
		# Keep a pure copy
		self.original_image_map = self.image_map.copy()
	
	"""
	The purpose of this method is to take all the placed images on the screen and scale them up or down for exporting.
	"""
	def export_image(self):
		
		# In future show an error message to the user.
		if self.current_container_image == None:
			return
			
		# Load the container image
		#base_data = self.current_container_image.load()
		
		# Scale the Frame up to the desired ratio
		temp_image = self.current_container_image.resize((int(self.current_container_image.width * self.image_scale), int(self.current_container_image.height * self.image_scale)), Image.ANTIALIAS)
		
		# Well we got the Big Show. It's time to put that image together
		export_width = temp_image.width
		export_height = temp_image.height
		
		# Create the skin for our output image.
		export_image = Image.new(mode = "RGBA", size = (export_width, export_height))
		export_data = export_image.load()
		
		# Place the image of the Frame
		for x in range(export_width):
			for y in range(export_height):
				export_data[x, y] = temp_image.getpixel((x,y))
				
		# Copy a scaled map for our reference
		scaled_map = self.original_image_map.copy()
		
		# Scale those up/down to the current defined ratio
		for k, v in self.original_image_map.items():
		
			#
			units = self.dragging_image_unit_map[k]
			print("{}x{}-{}".format(k, v, units))
			scaled_map[k] = v[0].resize((int(self.rack_unit_1u_width * self.image_scale), int((self.rack_unit_1u_height * units) * self.image_scale)), Image.ANTIALIAS)

		# Now we're going to take each image that was assigned to a rack unit space and paint it on this output image.
		for k, v in self.rack_unit_arr.items():
		
						
			# The first element i the key for self.rack_unit_arr is a image tracking variable used by the canvas to draw images.
			if v[1] > -1:

				# Grab the image
				if not v[2] == None:
					
					# The second element in the key for self.rack_unit_arr is a regular Image, not PhotoImage.
					img = scaled_map[v[0]]
					units = self.dragging_image_unit_map[v[0]]
					
					# Get the image data ready.
					img_data = img.load()
					print("IMG Data: {}x{}".format(img.width, img.height))
					
					# Let's define some offsets so that the rack unit image is drawn at the correct position.
					offset_x = int(self.rack_sample_wall_width * self.image_scale)
					offset_y = int(((self.rack_unit_1u_height) * k) * self.image_scale)
					
					# Take each pixel of the image and draw it on the export image. If I learn how to use the put method we will
					# do that instead of this.
					for x in range(img.width):
						for y in range(img.height):
							export_data[offset_x + x, int((self.rack_unit_1u_height * self.image_scale) + offset_y) + y] = img.getpixel((x,y))
		
		# Save wherever you want as whatever you want, but it must be a support file type.
		fname = filedialog.asksaveasfilename(parent = self.master, title = "Save Image As", defaultextension = ".png", filetypes = (("PNG", "*.png"), ("JPEG File", "*.jpg"), ("All others", "*.*")))
		
		# [DEBUG]
		print(f"Export Filename: {fname}")
		
		# SAVE TO FILE to the output directory
		export_image.save(os.path.join(self.dir_path_output, fname))

	def read_container_def_file(self, file):
			
		# Our output array will be structured as such
		# [0] = Rack Model
		# [1] = Rack Image File Name
		# [2] = Rack Units
		# [3] = Rack Height
		# [4] = Rack Width
		# [5] = Rack Lip Height Top
		# [6] = Rack Lip Height Bot
		# [7] = Rack Wall Width
		output = [-1] * 8
	
		# The classic with no ignore erros, because we want to know.
		with open(file, 'r') as input:
			
			# Read each line and challenge it
			for line in input:

				# Strip some things from the line
				line = line.replace("\n","")
				line = line.strip()
				
				# The Challenges
				if "=" in line:
					
					# Cutting the string up
					split = line.split("=")
					key = split[0].strip()
					value = split[1].strip()

					# Boy do I miss switches and cases, but at the same time... I don't
					if key == "rack_model":
						output[0] = value
					elif key == "rack_image":
						output[1] = value
					elif key == "rack_units":
						output[2] = int(value)
					elif key == "rack_height":
						output[3] = float(value)
					elif key == "rack_width":
						output[4] = float(value)
					elif key == "rack_lip_height_top":
						output[5] = float(value)
					elif key == "rack_lip_height_bot":
						output[6] = float(value)
					elif key == "rack_wall_width":
						output[7] = float(value)
						
		# Return the parsed values
		return output
		
	def __change_scale(self, event):
	
		#
		self.image_scale = float(self.combobox_scale.get().replace("%", "")) / 100
		print("New Scale: {}".format(self.image_scale))

	def _get_bbox_at_position(self, x, y):
		
		# Get the current mouse position
		for iter in range(len(self.bboxes)):
			
			# Grab that bounding box
			box = self.bboxes[iter]

			# Check collision
			if x >= box[0] and x <= box[2] and y >= box[1] and y <= box[3]:
				
				# Change the selected Rack Unit.
				return box

	def motion(self, event):

		# Update the mouse position
		self.mouse_x,self.mouse_y = event.x, event.y

		# I have a more efficient way to check arrays on motion events and I'll add it in a later revision
		for iter in range(len(self.rectangles)):
			coords = self.canvas.coords(self.rectangles[iter])
			if self.mouse_x > coords[0] and self.mouse_x < coords[2] and self.mouse_y > coords[1] and self.mouse_y < coords[3]:
				self.canvas.itemconfig(self.rectangles[iter], fill="Blue")
				self.canvas.itemconfig(self.runits[iter], fill="Red")
			elif self.canvas.itemcget(self.rectangles[iter], "fill") == "Blue":
				self.canvas.itemconfig(self.rectangles[iter], fill="Red")
				self.canvas.itemconfig(self.runits[iter], fill="Black")
		
		# Also if you're dragging then show something to let the user know that they're carrying something
		if self.dragging:
			if not self.dragging_image == None and not self.dragging_image_tracker == None:
				self.canvas.coords(self.dragging_image_tracker, event.x, event.y)

# Start from CMD like me?
if __name__=='__main__':
	mf = MainFrame(Tk())
