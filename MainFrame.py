from tkinter import *
from tkinter import ttk, font, messagebox, filedialog
from PIL import Image, ImageTk
import os, math

# Globals
DPI = 96

class MainFrame(Frame):

  # Variable Declaration
  # Data Types
  dragging=False
  dragging_units = 1
  # TKinter widgets
  canvas=None
  treeview_node_root = None
  treeview_main = None
  #
  rack_model = None
  rack_units = 0
  rack_real_wall_width = 0
  rack_real_width = 0
  rack_real_height = 0
  rack_real_lip_height_top = 0
  rack_real_lip_height_bot = 0
  rack_unit_1u_height = 0
  rack_sample_wall_width = 0
  rack_sample_lip_height_top = 0
  rack_sample_lip_height_bot = 0
  selected_rack_unit=None
  # Our BBOX array
  bboxes = []
  rectangles = []
  mouse_x=0
  mouse_y=0
  # These are more static, but of course there are different Rack Unit sizes.
  RACK_UNIT_HEIGHT_in = 1.75
  RACK_UNIT_WIDTH_in = 18.7
  # Images
  base_image=None
  base_photo=None
  dragging_fname=None
  dragging_image=None
  dragging_image_tracker=-1
  # Maps
  dragging_image_unit_map={}
  image_map_resized={}
  rack_unit_arr={}
  test_image_map={}
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
    display_wth = self.winfo_screenwidth()
    display_hgt = self.winfo_screenheight()
    frame_wth = display_wth // 2
    frame_hgt = display_hgt // 2
    frame_wht_info = frame_wth
    frame_hgt_info = 8
    frame_wht_image = frame_wth * .3 #96       
    frame_hgt_image = frame_hgt - frame_hgt_info
    cnvs_wth = frame_wth - frame_wht_image
    cnvs_hgt = frame_hgt - frame_hgt_info

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
    frame_info = Frame(self, width = frame_wht_info, height = frame_hgt_info, bd = 0, relief = RAISED)
    label_mouse = Label(frame_info, text="TEST")
    button = Button(frame_info, command=self.export_image)
    button.pack(side=LEFT, anchor='w')
    frame_info.pack(side = TOP, anchor='n')
    
    # Create the Frame on the left side of the screen that will handle the loaded files and allow for dragging and dropping. 
    frame_image = Frame(self, width = frame_wht_image, height = frame_hgt_image, bd = 1, relief=RAISED)             
    self.treeview_main = ttk.Treeview(frame_image, height = frame_hgt_image)
    self.treeview_main['columns']=("RU")
    self.treeview_main.column("RU", width = treeview_font.measure("Units") + 4)
    self.treeview_main.heading("RU", text = "Units")
    self.treeview_main.pack()
    frame_image.pack(side = LEFT, anchor = 'w')

    # [Temp] This is for the space being used by the Canvas on the frame.
    #cnvs_wth = frame_wth - frame_image.cget('width') - treeview_font.measure("*" * 32)
    
    # Define the root node
    self.treeview_node_root = self.treeview_main.insert('','end', text=f"{os.getcwd()}", tags=('touch'))
    
    # Bind the button press event to track dragging
    self.treeview_main.tag_bind('touch', '<Button-1>', self._tracking_enable)

    # Make the Canvas after all that
    frame_canvas = Frame(self, width = cnvs_wth, height = cnvs_hgt, bd = 1, relief = RAISED)
    self.canvas = Canvas(frame_canvas, width = cnvs_wth-2, height = cnvs_hgt-2)
    self.canvas.pack()
    frame_canvas.pack(side = RIGHT, anchor = 'e')
    
    # This will hold all of the images for the Containers
    #container_box = ttk.Combobox(frame_info)
    #container_box.pack(side=LEFT, anchor = 'w')

    # We will keep a map of Container to Container Definition Files and display the
    # Cooresponding CDF file as a label
    #cdfLabel = Label(text='A')

    # [Button Bindings]
    self.canvas.bind("<Button-1>", self._add_rack_unit)
    self.canvas.bind("<Button-3>", self._remove_rack_unit)
    self.canvas.bind("<Motion>", self.motion)                             
    
    # Attempt to import the network images
    self.import_images(self.dir_path_img)

    # Attempt to read the Rack Configuration file <- Will be a list of possible Racks in future.
    self.read_container_def_file(os.path.join(self.dir_path_input, "test.cdf"))
    
    # Each Rack unit will have multiple images and files associated.
    for i in range(self.rack_units):
      self.rack_unit_arr[i] = (None,-1, None)

    # The difference between the workspace and the contaner is that the workspace is the area used only for the
    # Rack Units and the Container describes the Real Life IDF or other Container for the Rack units
    cntr_wth_wall = self.rack_real_wall_width * DPI
    cntr_hgt_lip_top = self.rack_real_lip_height_top * DPI
    cntr_hgt_lip_bot = self.rack_real_lip_height_bot * DPI
    cntr_wth = self.rack_real_width * DPI
    cntr_hgt = self.rack_real_height * DPI
    
    # Define the workspace by removing the wall width and the top and bottom lips
    work_wth = cntr_wth - (cntr_wth_wall * 2)
    work_hgt = cntr_hgt - (cntr_hgt_lip_top + cntr_hgt_lip_bot)

    # Cut off any extra trim and get each variable down to a multiple of 10.
    work_wth = work_wth - (work_wth % 10)
    work_hgt = work_hgt - (work_hgt % 10)
    cntr_wth_wall = cntr_wth_wall - (cntr_wth_wall % 10)
    cntr_hgt_lip_top = cntr_hgt_lip_top - (cntr_hgt_lip_top % 10)
    cntr_hgt_lip_bot = cntr_hgt_lip_bot - (cntr_hgt_lip_bot % 10)
    cntr_wth = cntr_wth - (cntr_wth % 10)
    cntr_hgt = cntr_hgt - (cntr_hgt % 10)

    # Scaling Variables
    scale_counter = 0    
    w_temp = cntr_wth
    h_temp = cntr_hgt
    scale_factor = cntr_wth / cntr_hgt
    
    # Now we need to scale that up or down based on the canvas size
    if w_temp >= h_temp:
      if w_temp > cnvs_wth:
        while w_temp > cnvs_wth:
          w_temp = w_temp * scale_factor
          scale_counter = scale_counter + 1
    else:
      if h_temp > cnvs_hgt:
        while h_temp > cnvs_hgt:
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
    
    # Let's plot out some locations for the rectangles
    cntr_stx = (cnvs_wth // 2) + (cntr_wth // 2)
    cntr_sty = (cnvs_hgt // 2) - (cntr_hgt // 2)
    work_stx = cntr_stx - (cntr_wth // 2)
    work_sty = ((cnvs_hgt - cntr_hgt) // 2) + cntr_hgt_lip_top
    
    # Creation of the RED Rack Units as well as the definition of what self.rack_unit_1u_height will be for rest of program.
    self._create_container_image(cnvs_wth, cnvs_hgt, cntr_wth, cntr_hgt, cntr_stx, cntr_sty, work_wth, work_hgt, work_stx, work_sty)    
    
    # Once we have the frame resized we should also have a definite 1U height set to use to resize the images.
    self._create_resized_images(int(work_wth), int(work_hgt))

    # Pack and start
    self.pack(fill = BOTH)
    self.master.resizable(False, False)
    self.mainloop()

  def _create_container_image(self, cnvs_wth, cnvs_hgt, cntr_wth, cntr_hgt, cntr_stx, cntr_sty, work_wth, work_hgt, work_stx, work_sty):
    
    # Determine the size of 1 Rack Unit. If its not an integer then round it up and adjust the work and container height to fit.
    self.rack_unit_1u_height = math.ceil(work_hgt / self.rack_units)
    work_hgt = self.rack_unit_1u_height * self.rack_units
    cntr_hgt = work_hgt + self.rack_sample_lip_height_top + self.rack_sample_lip_height_bot
    print(f"RU1: {self.rack_unit_1u_height}")
    
    # This is a one-liner for opening the image, then resizing it and we keep the reference for the PhotoImage
    # So that it does not get Garbage Collected.
    self.base_image = Image.open(os.path.join(self.dir_path_input, "IDF_Base.png")).resize((int(cntr_wth), int(cntr_hgt)), Image.ANTIALIAS)
    self.base_photo = ImageTk.PhotoImage(self.base_image)

    # Create the image in the center of the canvas for the resized container.
    self.canvas.create_image(cntr_stx - (cntr_wth // 2), cntr_sty + (cntr_hgt // 2), image = self.base_photo)
    #self.canvas.create_rectangle(1, 1, cnvs_wth - 8, cnvs_hgt - 8)

    # Depending on the number of Rack Units possible for this Frame.
    for iter in range(self.rack_units):

      # Define the boundaries for the BBOX.
      x = work_stx - (work_wth // 2)
      y = (work_sty) + (iter * self.rack_unit_1u_height)
      wth = work_stx + (work_wth // 2)
      hgt = (work_sty) + ((iter * self.rack_unit_1u_height) + self.rack_unit_1u_height)

      # Define the BBOX
      box = (x, y, wth, hgt)
      
      # We need these rectangles for drawing.
      rectangle = self.canvas.create_rectangle(box[0],box[1],box[2],box[3], fill = "red")

      # We need the bboxes for mouse entry detection.
      self.bboxes.append(box)
      self.rectangles.append(rectangle)
    
    # Important Measurement here. This describes our programs usable rack wall width which will determine our
    # positioning during the export of the image
    self.rack_sample_wall_width = (cntr_wth - work_wth) // 2
  
  def _create_resized_images(self, width, height):

    # In a future revision each image will need a config file with it to determine the number of rack units to use
    for k, v in self.test_image_map.items():
      
      # Parse the Number of Rack units from the name
      units = 1
      
      # Just skip if ill-formated.
      try:

        # Grab the number of Rack Units from file name; ignore files without this format
        units = int(os.path.basename(k).split("_")[0])
        
        # Why this dictionary? This keeps a track of how many RUs each file takes up.
        self.dragging_image_unit_map[k] = units
      except ValueError:
        #print("Failed to parse")
        continue
        
      # Open the Image up and resize it to the size of a 1U Rack * How many units it thinks it is.
      img = Image.open(k)
      img = img.resize((int(width), int(math.ceil(self.rack_unit_1u_height * units))), Image.ANTIALIAS)

      # Not advised, but I re-assigned a tuple to a new tuple with a new size.      
      tup = self.test_image_map[k]

      # TESTING, if this works then get rid of image_map_resized
      self.test_image_map[k] = (tup[0], tup[1], img)
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
    
    print(f"Over-lapping Items: {item}")
    # Not hovering over anything? Stop.
    if item == None:
      return

    # We're going to use the keys to mark the RUs for deletion
    keys = self.rack_unit_arr.keys()
    rs = []

    # Now check the list of rack units for any that match what was clicked.
    for itr in keys:
      
      # Does it exist in the rack unit arr
      for index in item:

        # The way we setup rack_unir_arr is (fname, image_tracker, image)
        if self.rack_unit_arr[itr][1] == index: 
          
          # The result set is the rack unit index to clear out and the canvas image to remove.
          rs.append((itr, self.rack_unit_arr[itr][1]))
    
    # Do it after
    for r in rs:

      # The First image on the Canvas is the Frame (1). Following after are the Rack Units. What's left is all user-created.
      if r[1] > (self.rack_units + 1):
        self.canvas.delete(r[1])
        self.rack_unit_arr[r[0]] = (None, -1, None)

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
    #   return
    
    # Define the offset between each bbox
    offset = self.rack_unit_1u_height * self.dragging_units

    # Relate the image that your dropping with the rack unit you're over
    # This array is tracking the File Name of the image we're dragging, the canvas image tracker, the image, and the position
    self.rack_unit_arr[bbox_index] = (self.dragging_fname, self.dragging_image_tracker, self.dragging_image)    
    
    # Snap the image to the location of the bbox
    self.canvas.coords(self.dragging_image_tracker, ((bbox[0] + bbox[2]) //2,  bbox[1] + (offset // 2)))
      
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
      self.dragging_image_tracker = self.canvas.create_image(32, 32, image = self.dragging_image)
      self.dragging_units = int(self.dragging_image_unit_map[fname])

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
          self.test_image_map[fil] = (image_pil, image_tk)
  
  def export_image(self):

    # Load the container image
    base_data = self.base_image.load()
    
    # Well we got the Big Show. It's time to put that image together
    export_width = self.base_image.width
    export_height = self.base_image.height
    
    # Create the skin for our output image.
    export_image = Image.new(mode = "RGBA", size = (export_width, export_height))
    export_data = export_image.load()

    # Place the image of the Frame
    for x in range(export_width):
      for y in range(export_height):
        export_data[x, y] = self.base_image.getpixel((x,y))

    # Now we're going to take each image that was assigned to a rack unit space and paint it on this output image.
    for k, v in self.rack_unit_arr.items():
      
      # Print the item
      #print(f"DEBUG: {k}|{v}")
      
      # The first element i the key for self.rack_unit_arr is a image tracking variable used by the canvas to draw images.
      if v[1] > -1:

        # Grab the image
        if not v[2] == None:
          
          # The second element in the key for self.rack_unit_arr is a regular Image, not PhotoImage.
          img = self.test_image_map[v[0]][2]
          
          # Get the image data ready.
          img_data = img.load()
          
          # Let's define some offsets so that the rack unit image is drawn at the correct position.
          offset_x = self.rack_sample_wall_width
          offset_y = self.rack_unit_1u_height * k
          
          # Take each pixel of the image and draw it on the export image. If I learn how to use the put method we will
          # do that instead of this.
          for x in range(img.width):
            for y in range(img.height):
              export_data[offset_x + x, (self.rack_unit_1u_height + offset_y) + y] = img.getpixel((x,y))
    
    # Save wherever you want as whatever you want, but it must be a support file type.
    fname = filedialog.asksaveasfilename(parent = self.master,\
            title = "Save Image As", defaultextension = ".png",\
            filetypes = (("Portable Network Graphic", "*.png"),\
                         ("JPEG File", "*.jpg"),\
                         ("All others", "*.*")))
    
    # [DEBUG]
    print(f"Export Filename: {fname}")
    
    # SAVE TO FILE to the output directory
    export_image.save(os.path.join(self.dir_path_output, fname))

  def read_container_def_file(self, file):
      
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
            self.rack_model = value
          elif key == "rack_units":
            self.rack_units = int(value)
          elif key == "rack_width":
            self.rack_real_width = float(value)
          elif key == "rack_height":
            self.rack_real_height = float(value)
          elif key == "rack_lip_height_top":
            self.rack_real_lip_height_top = float(value)
          elif key == "rack_lip_height_bot":
            self.rack_real_lip_height_bot = float(value)
          elif key == "rack_wall_width":
            self.rack_real_wall_width = float(value)

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
    for rect in self.rectangles:
      coords = self.canvas.coords(rect)
      if self.mouse_x > coords[0] and self.mouse_x < coords[2] and self.mouse_y > coords[1] and self.mouse_y < coords[3]:
        self.canvas.itemconfig(rect, fill="Blue")
      elif self.canvas.itemcget(rect, "fill") == "Blue":
        self.canvas.itemconfig(rect, fill="Red")
    
    # Also if you're dragging then show something to let the user know that they're carrying something
    if self.dragging:
      if not self.dragging_image == None and not self.dragging_image_tracker == None:
        self.canvas.coords(self.dragging_image_tracker, event.x, event.y)

if __name__=='__main__':
  mf = MainFrame(Tk())
