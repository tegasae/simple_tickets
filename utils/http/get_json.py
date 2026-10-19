import asyncio
import httpx
from openpyxl import Workbook
URL="http://0.0.0.0:8000/openapi.json"

async def get_json(client: httpx.AsyncClient,url:str)->dict:
    response=await client.get(url)
    response.raise_for_status()
    return response.json()


async def parse()->list:
    n=[]
    async with httpx.AsyncClient(timeout=10.0) as client:
        data=await get_json(client,URL)
    paths=data['paths']

    for path in paths:
        for method in paths[path]:
            element=(path, method, paths[path][method]['operationId'])
            print(element)
            n.append(element)
    return n

def create_xls(n:list,name:str):
    wb=Workbook()
    ws=wb.active
    for r in n:
        ws.append([None,str(r[1]).upper(),r[0],r[2]])
    wb.save(name)


async def main():
    n=await parse()
    create_xls(n,"paths.xlsx")


asyncio.run(main())






