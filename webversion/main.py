from fileinput import filename
from typing import Union, Dict, List

from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, FilePath

from typing import List
import string
import random
import os
import shutil

import adumanisMain

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}

@app.post("/uploadmultifile")
async def upload(files: List[UploadFile] = File(...)):
    if (len(files)) > 0 :
        for data in files:
            if (data.filename ==""):
                return {"message":"No files uploaded"}

    lenRandom = 10
    ran = ''.join((random.choice(string.ascii_lowercase) for x in range(lenRandom)))  

    try:
        os.mkdir(ran)
    
    except Exception:
        return {"message": "Fail to create directory!"}
    
    for file in files:
        try:
            file_name= ran+file.filename
            file_location = f"{ran}/{file_name}"
            contents = await file.read()
            with open(file_location, "wb+") as file_obj:
                file_obj.write(contents)

        except Exception:
            return {"message": "There was an error uploading the file(s)"}
        finally:
            # shutil.move(file.filename,ran+"/"+file.filename)
            await file.close()
    
    msg = {"message": "Successfully uploaded", "random": ran}
    data = f"{[file.filename for file in files]}"

    # return {"message": f"Successfuly uploaded {[file.filename for file in files]}"}
    return msg, data

class Parameter(BaseModel):
    id_file: str
    # tollerance: float
    # nibkontrol: str
    # weight: Union[str, None] = None


@app.post("/adumanis")
def adumanis_process(
    tollerance: float = Form(...),
    id_file: str = Form(...),
    nibcontrol: str = Form(...),
    weight: float = Form(...)
    ):

    nib = nibcontrol.split(";")
    datacontrol = []
    for temp in nib:
        datacontrol.append(temp.strip())

    hasil =  adumanisMain.adumanis_process (id_file, datacontrol, tollerance, weight)
    return hasil


@app.get("/random")
def randomGen():
    lenRandom = 10
    ran = ''.join((random.choice(string.ascii_lowercase) for x in range(lenRandom)))  
    return {"message": f"{ran}"}



@app.get("/upload")
async def uploadfile():
    content = """
<body>
<h2>Ini form upload files</h2>

<form action="/uploadmultifile/" enctype="multipart/form-data" method="post">
<p>Upload file .shp, .shx, .dbf (.cpg, .qmd optional)</p>
<input name="files" type="file" multiple>
<input type="Submit" value="Upload">
</form>

<h2>Proses Adumanis</h2>
<form action="http://adumanis.com:8000/adumanis" method="post">
<p>
Random ID
<input name="id_file" type="text" value="rfncyghdmf">
</p>
<p>
<input name="tollerance" type="text" placeholder="input distance tollerance">
</p>
<p>
Pisahkan nomor NIB dengan tanda titik koma (;) jika terdapat lebih dari 1 persil<br>
<input name="nibcontrol" type="text" placeholder="NIB Kontrol">
</p>
<p>
<input name="weight" type="text" placeholder="input weight">
</p>
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)
