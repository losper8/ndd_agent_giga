from datetime import datetime
from typing import List

from aiohttp import ClientSession

from common.domain.schema import Patent, SearchPatentResponse
from common.utils.debug import async_timer
from rospatent_scraper.domain.schema import SearchPatentsRequest


@async_timer
async def search_patents(request: SearchPatentsRequest, session: ClientSession) -> SearchPatentResponse:
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
        'limit': request.limit,
        'offset': request.offset,
        'pre_tag': '',
        'post_tag': '',
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
        "https://searchplatform.rospatent.gov.ru/search",
        headers=headers,
        params=params,
        json=data_row,
        verify_ssl=False,
        timeout=420000
    ) as response:
        response_json = await response.json(content_type=None)
        # print(response_json)
        for hit in response_json['hits']:
            total = response_json['total']
            id_ = hit['id']
            snippet = hit['snippet']
            title = snippet['title']
            snipped_description = snippet['description']

            common = hit['common']
            application = common.get('application', {})
            application_number = application.get('number', None)
            application_filing_date = datetime.strptime(application['filing_date'], "%Y.%m.%d") if application.get('filing_date') else None

            publication_date = datetime.strptime(common['publication_date'], "%Y.%m.%d")

            classification = common.get('classification', {})
            ipc = classification.get('ipc', None)
            if ipc:
                ipc = [current['fullname'] for current in ipc]

            cpc = classification.get('cpc', None)
            if cpc:
                cpc = [current['fullname'] for current in cpc]

            biblio = hit['biblio']
            biblio_ru = biblio.get('ru', None)
            biblio_en = biblio.get('en', None)

            title_ru, title_en = None, None
            patentees_ru, applicants_ru, inventors_ru = None, None, None
            patentees_en, applicants_en, inventors_en = None, None, None

            if biblio_ru:
                title_ru = biblio_ru.get('title', None)
                patentee_ru = biblio_ru.get('patentee', None)
                if patentee_ru:
                    patentees_ru = [current['name'] for current in patentee_ru]

                applicant_ru = biblio_ru.get('applicant', None)
                if applicant_ru:
                    applicants_ru = [current['name'] for current in applicant_ru]

                inventor_ru = biblio_ru.get('inventor', None)
                if inventor_ru:
                    inventors_ru = [current['name'] for current in inventor_ru]

            if biblio_en:
                title_en = biblio_en.get('title', None)
                patentee_en = biblio_en.get('patentee', None)
                if patentee_en:
                    patentees_en = [current['name'] for current in patentee_en]

                applicant_en = biblio_en.get('applicant', None)
                if applicant_en:
                    applicants_en = [current['name'] for current in applicant_en]

                inventor_en = biblio_en.get('inventor', None)
                if inventor_en:
                    inventors_en = [current['name'] for current in inventor_en]

            results.append(
                Patent(
                    id=id_,
                    title_ru=title_ru,
                    title_en=title_en,
                    publication_date=publication_date,
                    application_number=application_number,
                    application_filing_date=application_filing_date,
                    ipc=ipc,
                    cpc=cpc,
                    snippet_ru=snipped_description,
                    patentees_ru=patentees_ru,
                    patentees_en=patentees_en,
                    applicants_ru=applicants_ru,
                    applicants_en=applicants_en,
                    inventors_ru=inventors_ru,
                    inventors_en=inventors_en,
                )
            )
    return SearchPatentResponse(
        total=total,
        patents=results
    )
