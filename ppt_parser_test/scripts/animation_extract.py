from lxml import etree
import zipfile

with zipfile.ZipFile("input/ppt/input.pptx", "r") as z:
    xml_data = z.read("ppt/slides/slide1.xml")
    root = etree.fromstring(xml_data)
    pretty = etree.tostring(root, pretty_print=True, encoding="utf-8").decode("utf-8")
    print(pretty[:10000])  # 앞부분만 출력
