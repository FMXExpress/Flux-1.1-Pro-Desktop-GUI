import os
import replicate
import urllib.request
import hashlib
from delphifmx import *

# Set the API token for Replicate
os.environ["REPLICATE_API_TOKEN"] = "replicate_com_api_key"

class TextPromptApp(Form):

    def __init__(self, owner):
        # Setting up the style and form properties
        self.stylemanager = StyleManager(self)
        self.stylemanager.SetStyleFromFile("Air.style")

        self.SetProps(Caption="Flux 1.1 Pro + Replicate API", OnShow=self.__form_show, OnClose=self.__form_close)

        # Layout for the top components (Button and Label)
        self.layout_top = Layout(self)
        self.layout_top.SetProps(Parent=self, Align="Top", Height="50", Margins=Bounds(RectF(3, 3, 3, 3)))

        # Label to prompt the user
        self.prompt_label = Label(self)
        self.prompt_label.SetProps(Parent=self.layout_top, Align="Left", Text="Enter your prompt:", Position=Position(PointF(20, 20)), Margins=Bounds(RectF(3, 3, 3, 3)))

        # Memo control to take the text prompt
        self.prompt_memo = Memo(self)
        self.prompt_memo.SetProps(Parent=self, Align="Left", Position=Position(PointF(20, 60)), Width=300, Height=150, Margins=Bounds(RectF(3, 3, 3, 3)), WordWrap=True,
        Text="A young, vibrant magical Fire Monkey wearing a hoplite helmet and with soft, glowing fur that transitions from fiery red at the tips to a warm orange near its body, sits perched playfully with a mischievous grin. Its expressive golden eyes sparkle with curiosity and affection, small flames gently flicker around its ears, and a subtle shimmer of magic radiates from its fur. The monkey's posture is dynamic, one paw resting on its chest while the other extends outward as if offering a gesture of friendship. Soft, diffused twilight lighting casts a gentle glow across its face, creating a cozy, enchanted atmosphere with a lush jungle and exploding volcano backdrop in the distance.")


        # Image control for the upscaled image display
        self.img = ImageControl(self)
        self.img.SetProps(Parent=self, Align="Client", Position=Position(PointF(340, 60)), Width=300, Height=300, Margins=Bounds(RectF(3, 3, 3, 3)))

        # Button to trigger the prompt processing
        self.send_button = Button(self)
        self.send_button.SetProps(Parent=self.layout_top, Align="Right", Text="Send Prompt", Position=Position(PointF(290, 18)), Width=120, OnClick=self.__send_prompt, Margins=Bounds(RectF(3, 3, 3, 3)))

        # Status bar at the bottom
        self.status_bar = Label(self)
        self.status_bar.SetProps(Parent=self, Align="Bottom", Text="Status: Ready", Height=30, Margins=Bounds(RectF(3, 3, 3, 3)))

        # Timer for updating the status periodically
        self.timer = Timer(self)
        self.timer.Interval = 1000  # Timer event will trigger every second
        self.timer.Enabled = False
        self.timer.OnTimer = self.__on_timer_tick

        # Initialize variables for prediction handling
        self.prediction = None

    def __form_show(self, sender):
        self.SetProps(Width=700, Height=400)

    def __form_close(self, sender, action):
        self.timer.Enabled = False
        action = "caFree"

    def __send_prompt(self, sender):
        self.timer.Enabled = False

        prompt = self.prompt_memo.Text.strip()
        if not prompt:
            self.status_bar.Text = "Status: Please enter a valid text prompt."
            return

        self.status_bar.Text = "Status: Sending prompt to model..."
        self.send_button.Enabled = False  # Disable send button during processing
        Application.ProcessMessages()

        self.__start_prompt_process(prompt)

    def __start_prompt_process(self, prompt):
        try:
            # Use Replicate to send the text prompt
            model = replicate.models.get("black-forest-labs/flux-1.1-pro")
            #version = model.versions.get("")
            #versions = model.versions.list()
            #version = versions[0]
            self.prediction = replicate.predictions.create(
                model=model,
                input={"prompt": prompt,
                        "aspect_ratio": "1:1",
                        "output_format": "png",
                        "output_quality": 80,
                        "safety_tolerance": 2,
                        "prompt_upsampling": True
                }
            )
            self.timer.Enabled = True  # Enable the timer to start checking the status
        except Exception as e:
            self.status_bar.Text = f"Status: Error occurred - {str(e)}"
            self.send_button.Enabled = True  # Re-enable the send button

    def __on_timer_tick(self, sender):
        if self.prediction is None:
            return

        try:
            self.prediction.reload()  # Reload status periodically
            if self.prediction.status == "processing":
                status = self.prediction.status
                self.status_bar.Text = f"Status: {status}..."

            elif self.prediction.status in ["succeeded", "failed", "canceled"]:
                self.timer.Enabled = False  # Disable the timer when the process finishes
                if self.prediction.status == "succeeded":
                    image_url = self.prediction.output  # Assuming the output is the URL
                    file_name = './' + hashlib.md5(image_url.encode()).hexdigest() + '.png'
                    urllib.request.urlretrieve(image_url, file_name)

                    # Display the upscaled image
                    self.img.LoadFromFile(file_name)
                    self.status_bar.Text = "Status: Complete!"
                else:
                    self.status_bar.Text = f"Status: Process failed with status: {self.prediction.status}"
                self.send_button.Enabled = True  # Re-enable the send button
        except Exception as e:
            self.status_bar.Text = f"Status: Error occurred - {str(e)}"
            self.timer.Enabled = False
            self.send_button.Enabled = True  # Re-enable the send button

def main():

    Application.Initialize()
    Application.Title = "Flux 1.1 Pro + Replicate API"
    Application.MainForm = TextPromptApp(Application)
    Application.MainForm.Show()
    Application.Run()
    Application.MainForm.Destroy()

if __name__ == '__main__':
    main()
