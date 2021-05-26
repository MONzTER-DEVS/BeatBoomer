from pypresence import Presence
import time


class RichPresence:
    def __init__(self):
        client_id = "846786017260208129"
        self.RPC = Presence(client_id)  # Initialize the client class
        self.RPC.connect()  # Start the handshake loop
        self.frame = 0
        self.RPC.update(
            state="Just started Playing...",
            details="Rhythm based hyper-casual game.",
            large_image="beatnboomwithbackbig",
            buttons=[{"label": "Download Now!", "url": "https://monzter-games.itch.io/beat-n-boom"}]
        )

    def update_rich_presence(self, state: str):
        self.frame += 1
        if self.frame > 100:
            self.frame = 0
            # print("UPDATING RP...")
            self.RPC.update(
                state=state,
                details="Rhythm based hyper-casual game.",
                large_image="beatnboomwithbackbig",
                buttons=[{"label": "Download Now!", "url": "https://monzter-games.itch.io/beat-n-boom"}]
            )
