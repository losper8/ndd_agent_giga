from datetime import datetime
from io import BytesIO
from typing import List

from aiohttp import ClientSession
from openpyxl import load_workbook

from common.utils.debug import async_timer
from rospatent_scraper.domain.schema import SearchPatentsRequest
from common.domain.schema import SearchPatentResponse, Patent


@async_timer
async def search_patents_xlsx(request: SearchPatentsRequest, session: ClientSession) -> SearchPatentResponse:
    total = 0
    results: List[Patent] = []

    headers = {'Content-Type': 'application/json'}
    params = {'t': int(datetime.now().timestamp() * 1000)}

    filter_ = {}
    if request.date_from or request.date_to:
        date_published_search_range = {}
        if request.date_from:
            date_published_search_range.update({'gte': request.date_from.strftime("%Y%m%d")})
        if request.date_to:
            date_published_search_range.update({'lte': request.date_to.strftime("%Y%m%d")})
        filter_.update(
            {
                'date_published:search': {
                    'range': date_published_search_range
                }
            }
        )
    if request.author:
        filter_.update(
            {
                'authors:search': {
                    'search': request.author,
                }
            }
        )

    data_row = {
        'format': 'xlsx',
        'limit': request.limit,
        'offset': request.offset,
        'fields': [
            'identity',
            'publication_date',
            'title',
            'application.number',
            'application.filing_date',
            # 'ipc',
            # 'applicant',
            # 'inventor',
            # 'patentee',
            'abstract',
        ],
        'sort': request.sort.value,
        'datasets': [dataset.value for dataset in request.datasets if dataset],
        'preffered_lang': 'ru',
    }
    if filter_:
        data_row.update({'filter': filter_})
    if request.patent_description:
        data_row.update({'qn': request.patent_description})
    # print(f'{data_row=}')

    async with session.post(
        "https://searchplatform.rospatent.gov.ru/report",
        headers=headers,
        params=params,
        json=data_row,
        verify_ssl=False,
    ) as response:
        pass
        workbook = load_workbook(BytesIO(await response.read()))
        sheet = workbook.active

        total = sheet['B3'].value
        # print(f'{total=}')

        for row in sheet['A9':f'F{8 + request.limit}']:
            row_data = [cell.value for cell in row]
            if all(element is None for element in row_data):
                break
            identity = row_data[0]
            publication_date = row_data[1]
            title = row_data[2]
            application_number = row_data[3]
            application_filing_date = row_data[4]
            abstract = row_data[5]
            # print(f'{identity=}, {publication_date=}, {title=}, {application_number=}, {application_filing_date=}, {abstract=}')
            identity_cleaned = identity.replace(' ', '')
            publication_date_cleaned = publication_date.replace('.', '')
            id_ = f'{identity_cleaned}_{publication_date_cleaned}'
            results.append(
                Patent(
                    id=id_,
                    title_ru=title,
                    publication_date=datetime.strptime(publication_date, '%Y.%m.%d'),
                    application_number=application_number,
                    application_filing_date=datetime.strptime(application_filing_date, '%Y.%m.%d') if application_filing_date else None,
                    abstract_ru=abstract,
                )
            )
    return SearchPatentResponse(
        total=total,
        patents=results
    )
