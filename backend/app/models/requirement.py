class Requirement:
    def __init__(self, req_id, req_type, text):
        self.id = req_id
        self.type = req_type
        self.text = text

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "text": self.text
        }