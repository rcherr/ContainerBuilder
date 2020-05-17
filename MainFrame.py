from tkinter import *
from tkinter import messagebox
from PIL import Image, ImageTk
import os

class MainFrame(Frame):

    # Variable Declaration
    rack_model = None
    rack_units = 0
    rack_wall_width_mm = 0
    rack_unit_fill_width_mm = 0
    rack_unit_fill_height_mm = 0
    rack_unit_gap_mm = 0
    rack_real_width_mm = 0
    rack_real_height_mm = 0
    rack_real_depth_mm = 0
    rack_point_pairs = None
    rack_lip_height_mm = 0
    selected_rack_unit=None
    # Our BBOX array
    bboxes = []
    mouse_x=0
    mouse_y=0
    # These are more static, but of course there are different Rack Unit sizes.
    RACK_UNIT_HEIGHT_in = 1.75
    RACK_UNIT_WIDTH_in = 18.7
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
        canvas_width = frame_width
        canvas_height = frame_height

        # Setup the dimensions for the Frame
        self.master.geometry("{}x{}+{}+{}".format(frame_width,\
                            frame_height, display_width//2-frame_width//2,\
                            display_height//2-frame_height//2))
        self.config(width = frame_width, height = frame_height)
        self.master.title("Container Builder")
        
        # Register a left-click for the rectangles being created
        #self.bind("<Button-1>", self.update_selected_button)
        #self.bind("<Motion>", self.motion)

        # Create the canvas
        canvas = Canvas(master, width = canvas_width, height = canvas_height)
        canvas.bind("<Button-1>", self.update_selected_button)
        canvas.bind("<Motion>", self.motion)
        canvas.pack()
        
        # Attempt to read the Rack Configuration file
        self.read_container_def_file(os.path.join(os.getcwd(), "test.cdf"))

        # Just a note that I have a problem with numbers so someone else will have to check these calculations
        # We need to now place the Big ole' container in the middle of the canvas.
        base_image = Image.open(os.path.join(os.getcwd(), "IDF_Base.png"))
        base_image_width = float(base_image.width)
        base_image_height = float(base_image.height)
        
        # Calculate the Aspect ratio for the rack provided.
        rack_aspect_ratio = float(self.rack_real_width_mm / self.rack_real_height_mm)
        rack_aspect_ratio = rack_aspect_ratio + .25 

        # Calculate a new height based on the real rack height
        new_width = int(float(base_image_width) * rack_aspect_ratio)
        new_height = int(float(base_image_height) * rack_aspect_ratio)
        
        # Where are we going to position the rack
        rack_posx = (canvas_width // 2)
        rack_posy = (canvas_height // 2)
        
        # What is the actual size of each rack unit on this scaled down image
        rack_unit_size_height = new_height - ((self.rack_lip_height_mm * rack_aspect_ratio) * 2)
        rack_unit_size_actual = rack_unit_size_height / self.rack_units

        # Where should we start the coords for the first rack unit
        rack_unit_start_x = rack_posx - new_width // 2
        rack_unit_start_y = rack_posy - (rack_unit_size_height // 2)

        # How much gap is in between each rack unit
        rack_unit_gap = self.rack_unit_gap_mm * rack_aspect_ratio
        rack_unit_gap = self.rack_unit_gap_mm / 25.4
        
        # What about the walls to the left and right of the container
        rack_wall_width = self.rack_wall_width_mm * rack_aspect_ratio

        # How long is each rack unit
        rack_unit_fill_width = new_width - (rack_wall_width * 2)
        rack_unit_fill_height = self.RACK_UNIT_HEIGHT_in * rack_aspect_ratio
        
        # I like to define the lip height as the area that is OOB for R-U's
        resized_image = base_image.resize((new_width, new_height), 1)
        
        # Create an image from that
        base_tk = ImageTk.PhotoImage(resized_image)

        # Pass that to the canvas to display and please make sure it's an integer.
        canvas.create_image(rack_posx, rack_posy, image = base_tk)
        
        # Once you read in that file then we can start to build the controls that be at those locations
        for iter in range(self.rack_units):

            #
            canvas.create_rectangle(\
                    rack_unit_start_x + rack_wall_width,\
                    rack_unit_start_y + (iter * rack_unit_size_actual) + 1,\
                    rack_unit_start_x + new_width - rack_wall_width,\
                    rack_unit_start_y + (iter * rack_unit_size_actual) + (rack_unit_size_actual + 1) - rack_unit_gap,\
                    fill = "red")
            box = (rack_unit_start_x + rack_wall_width,\
                    rack_unit_start_y + (iter * rack_unit_size_actual) + 1,\
                    rack_unit_start_x + new_width - rack_wall_width,\
                    rack_unit_start_y + (iter * rack_unit_size_actual) + (rack_unit_size_actual + 1) - rack_unit_gap)
            self.bboxes.append(box)

        for box in self.bboxes:
            print(box)

        # Pack and start
        self.pack(fill = BOTH, expand = 1)
        self.mainloop()

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
                        self.rack_real_width_mm = float(value) * 25.4
                    elif key == "rack_height":
                        self.rack_real_height_mm = float(value) * 25.4
                    elif key == "rack_depth":
                        self.rack_real_depth_mm == float(value) * 25.4
                    elif key == "rack_lip_height":
                        self.rack_lip_height_mm = float(value) * 25.4
                    elif key == "rack_wall_width":
                        self.rack_wall_width_mm = float(value) * 25.4
                    elif key == "rack_unit_gap":
                        self.rack_unit_gap_mm = float(value) * 25.4
                    elif key == "rack_point_pairs":
                        self.rack_point_pairs = self.parse_rack_points(value)

    def parse_rack_points(self, values):

        # Strip the brackets from them
        points = values.replace("[","").replace("]", "")

        # Attempt to split them up by commas
        points = points.split(",")

        # Build the points using the array but make sure there are an even number of points provided
        if len(points) % 2 == 0:
            
            # Our output variable
            output = []

            # Go over all the points but track with variable 'iter'
            for iter in range(len(points)):

                # If its odd then you must have gone over a point prior and that must be the pair
                if iter % 2 == 1:
                    output.append([int(points[iter-1]), int(points[iter])])
            
            # You're gonna be fine, bud.
            return output

        # You didn't get lucky, bud
        return None

    def update_selected_button(self, event):
        
        # Get the current mouse position
        for iter in range(len(self.bboxes)):
            
            # Grab that bounding box
            box = self.bboxes[iter]

            # Check collision
            if self.mouse_x >= box[0] and self.mouse_x <= box[2] and self.mouse_y >= box[1] and self.mouse_y <= box[3]:
                
                # Change the selected Rack Unit.
                self.selected_rack_unit = box

                # Show a message
                messagebox.showinfo(title="Rack Unit selected", message=f"{iter}")
                
                # Break out if you find a match.
                break

    def motion(self, event):

        # Update the mouse position
        self.mouse_x,self.mouse_y = event.x, event.y

if __name__=='__main__':
    mf = MainFrame(Tk())
