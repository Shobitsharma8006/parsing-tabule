import xml.etree.ElementTree as ET

class TableauXMLLoader:
    @staticmethod
    def load(path: str) -> ET.Element:
        tree = ET.parse(path)
        return tree.getroot()
