from tkinter import *
from tkinter import ttk, font, messagebox
from PIL import Image, ImageTk
import os, math

class MainFrame(Frame):

    # Variable Declaration
    # Data Types
    dragging=False
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
    dragging_image=None
    dragging_image_tracker=None
    image_map={}
    image_map_resized={}
    #
    img=None
    device_img=None
    # End of Variable Declaration
        
    def __init__(self, master):
        
        #
        Frame.__init__(self, master)
        self.master = master

        #
        frame_width = 640
        frame_height = 480
        display_width = self.winfo_screenwidth()
        display_height = self.winfo_screenheight()
        frame_info_width = frame_width
        frame_info_height = 24
        frame_image_width = 96             
        frame_image_height = frame_height - frame_info_height
        canvas_width = frame_width - frame_image_width
        canvas_height = frame_height - frame_info_height
        
        # Define some fonts for styling
        treeview_font = font.Font(family="Helvetica", size=7, weight="normal")
        treeview_heading_font = font.Font(family="Helvetica", size=8, weight="normal")
        # Define the style for the different widgets
        treeview_style = ttk.Style()
        treeview_style.configure("Treeview", font=treeview_font)
        treeview_heading_style = ttk.Style()
        treeview_heading_style.configure("Treeview.Heading", font=treeview_font)

        # Setup the dimensions for the Frame
        self.master.geometry("{}x{}+{}+{}".format(frame_width,\
                            frame_height, display_width//2-frame_width//2,\
                            display_height//2-frame_height//2))
        self.config(width = frame_width, height = frame_height)
        self.master.title("Container Builder")

        # Create the Frame that will host all of the information about what is going on the screen
        frame_info = Frame(self, width = frame_info_width, height = frame_info_height, bd = 1, relief = RAISED)
        label_mouse = Label(frame_info, text="TEST")
        #label_mouse.pack(side=LEFT)
        frame_info.pack(side = BOTTOM, anchor='s')
        
        # Create the Frame on the left side of the screen that will handle the loaded files and allow for dragging and dropping.  
        frame_image = Frame(self, width = frame_image_width, height = frame_image_height, bd=1, relief=RAISED)                         
        self.treeview_main = ttk.Treeview(frame_image, height = frame_image_height)
        self.treeview_main['columns']=("RU")
        self.treeview_main.column("RU", width = treeview_font.measure("Units") + 4)
        self.treeview_main.heading("RU", text = "Units")
        self.treeview_main.pack()
        frame_image.pack(side = LEFT, anchor = 'n')            
        
        # Define the root node
        self.treeview_node_root = self.treeview_main.insert('','end', text=f"{os.getcwd()}", tags=('touch'))
        
        # Bind the button press event to track dragging
        self.treeview_main.tag_bind('touch', '<Button-1>', self._tracking_enable)

        # Make the Canvas after all that
        frame_canvas = Frame(self, width = frame_width - frame_image.cget('width'), height = canvas_height, bd = 1, relief = RAISED)
        self.canvas = Canvas(frame_canvas, width = frame_width - frame_image.cget('width'), height = canvas_height)
        self.canvas.bind("<Button-1>", self.attempt_drop)
        self.canvas.bind("<Button-3>", self.clear_rack_unit)
        #self.canvas.bind("<ButtonRelease>", self.attempt_drop)
        self.canvas.bind("<Motion>", self.motion)                                                        
        self.canvas.pack()
        frame_canvas.pack(anchor='e')

        # Attempt to import the network images
        self.import_network_images(os.getcwd())

        # Attempt to read the Rack Configuration file
        self.read_container_def_file(os.path.join(os.getcwd(), "test.cdf"))
        
        # The difference between the workspace and the contaner is that the workspace is the area used only for the
        # Rack Units and the Container describes the Real Life IDF or other Container for the Rack units
        container_wall_width = self.rack_real_wall_width * 96
        container_lip_height_top = self.rack_real_lip_height_top * 96
        container_lip_height_bot = self.rack_real_lip_height_bot * 96
        container_total_width = self.rack_real_width * 96
        container_total_height = self.rack_real_height * 96

        # Define the workspace by removing the wall width and the top and bottom lips
        workspace_width = container_total_width - (container_wall_width * 2)
        workspace_height = container_total_height - (container_lip_height_top + container_lip_height_bot)
        
        # We're going to need this image available to scale it down.
        image_base_temp = Image.open(os.path.join(os.getcwd(), "IDF_Base.png"))
        image_base_width = image_base_temp.width
        image_base_height = image_base_temp.height

        # Vars
        scale_counter = 0        
        w_temp = container_total_width
        h_temp = container_total_height
        scale_factor = container_total_width / container_total_height
        
        # Now we need to scale that up or down based on the canvas size
        if w_temp >= h_temp:
            if w_temp > canvas_width:
                while w_temp > canvas_width:
                    w_temp = w_temp * scale_factor
                    scale_counter = scale_counter + 1
        else:
            if h_temp > canvas_height:
                while h_temp > canvas_height:
                    h_temp = h_temp * scale_factor
                    scale_counter = scale_counter + 1
        
        # Scale the workspace and the container down to fit the canvas.
        for i in range(scale_counter):
            workspace_width = workspace_width * scale_factor
            workspace_height = workspace_height * scale_factor
            container_wall_width = container_wall_width * scale_factor
            container_lip_height_top = container_lip_height_top * scale_factor
            container_lip_height_bot = container_lip_height_bot * scale_factor
            container_total_width = container_total_width * scale_factor
            container_total_height = container_total_height * scale_factor
        
        # When describing the Rack Units always use the workspace for reference dimensions
        rack_unit_1u_height = workspace_height / self.rack_units

        # Let us plot out some locations for the rectangles
        start_container_x = (canvas_width // 2) + (container_total_width // 2)
        start_container_y = (canvas_height // 2) - (container_total_height // 2)
        start_workspace_x = start_container_x - (container_total_width // 2)
        start_workspace_y = ((canvas_height - container_total_height) // 2) + container_lip_height_top
               
        # For this shit program we also need a version of the images scaled down to just slightly smaller than 1 Rack Unit height,
        # In a future revision each image will need a config file with it to determine the number of rack units to use
        for k, v in self.image_map.items():
            
            # Parse the Number of Rack units from the name
            units = 1
            
            try:
                units = int(k.split("_")[0])
            except ValueError:
                print("Failed to parse")
                continue

            # Have to do this a litte weird
            img = Image.open(k)
            img = img.resize((int(workspace_width), int(rack_unit_1u_height * units)), Image.ANTIALIAS)

            # Grab some variables we're going to use multiple times -_-            
            self.image_map_resized[k] = ImageTk.PhotoImage(img)
        
        # Create nodes based on those images
        for k, v in self.image_map.items():

            # Parse the Number of Rack units from the name
            units = 1

            try:
                units = int(k.split("_")[0])
            except ValueError:
                print("FaILED!")

                # If you didn't include the Rack Unit in the name then it gets skipped.
                continue

            # Scale the image to the width and height of the frame
            branch = self.treeview_main.insert(self.treeview_node_root, 'end', text=k, values=(f"{units}"), tags=('touch'))

        # Pass that to the canvas to display and please make sure it's an integer.
        image_base_temp = image_base_temp.resize((int(container_total_width), int(container_total_height)), Image.ANTIALIAS)
        image_base_resized = ImageTk.PhotoImage(image_base_temp)
        self.canvas.create_image(start_container_x - (container_total_width // 2),\
                start_container_y + (container_total_height // 2),\
                image = image_base_resized)
        
        # Once you read in that file then we can start to build the controls that be at those locations
        for iter in range(self.rack_units):

            # Create the bounding boxes for the Rack Units.
            box = (\
                    start_workspace_x - (workspace_width // 2),\
                    start_workspace_y + (iter * rack_unit_1u_height),\
                    start_workspace_x + (workspace_width // 2),\
                    start_workspace_y + ((iter * rack_unit_1u_height) + rack_unit_1u_height))
            rectangle = self.canvas.create_rectangle(box[0],box[1],box[2],box[3], fill = "red")
            self.bboxes.append(box)
            self.rectangles.append(rectangle)
        
        # Create Lines to make sure we're lining up right.
        self.canvas.create_line(0, start_workspace_y, canvas_width, start_workspace_y, fill="GREEN")
        self.canvas.create_line(start_workspace_x, 0, start_workspace_x, canvas_height, fill="BLACK")
        
        # Pack and start
        self.pack(fill = BOTH, expand = 1)
        self.mainloop()

    def clear_rack_unit(self, event):

        bbox = self.get_bbox_at_position(event.x, event.y)

        if not bbox == None:

            # Find what's at this location
            item = self.canvas.find_enclosed(bbox[0]-2,bbox[1]-2,bbox[2]+2,bbox[3]+2)
            print(item)
            for index in item:
                if self.canvas.type(index)=="image":
                    self.canvas.delete(index)

    def attempt_drop(self, event):
        
        #
        if self.dragging_image == None or self.dragging_image_tracker == None:
            return

        # Find out what we're hovering over
        bbox = self.get_bbox_at_position(event.x, event.y)

        # Is that a valid bbox?
        if not bbox == None:

            # Snap the image to the location of the bbox
            self.canvas.coords(self.dragging_image_tracker, (bbox[0] + bbox[2]) // 2, 1 + (bbox[1] + bbox[3]) // 2)
            
            # Let it sit where it is; later we will append this and the base_image to an array.
            self.dragging = False
            self.dragging_image = None
            self.dragging_image_tracker=None
        else:

            # Delete the hanging items
            self.canvas.delete(self.dragging_image_tracker)

    def _tracking_enable(self, event):
        
        # Grab the currently
        self.dragging = True
        self.canvas.delete(self.dragging_image_tracker)

        # Find what was selected
        selected_item = self.treeview_main.identify('item', event.x, event.y)

        # Kick out if there's not a valid selection.
        if selected_item == '':
            return

        # Grab the actual
        selected_node = self.treeview_main.item(selected_item)

        if selected_node['text'] in self.image_map_resized:

            # Grab the text
            self.dragging_image = self.image_map_resized[selected_node['text']]
            
            if not self.dragging_image == None:
            
                # Add that to the canvas
                self.dragging_image_tracker = self.canvas.create_image(32, 32, image = self.dragging_image)

    def import_network_images(self, dir):

        # Acceptable images types
        image_types = ['.png', '.jpeg', '.bmp', '.jpg']

        #
        for fil in os.listdir(dir):

            if os.path.isfile(fil):

                # Grab the extension
                ext = os.path.splitext(fil)[1]
                
                #
                if ext in image_types:
                    self.image_map[fil] = PhotoImage(file = fil)

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

    def get_bbox_at_position(self, x, y):
        
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