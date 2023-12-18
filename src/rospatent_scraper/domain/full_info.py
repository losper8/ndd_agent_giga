from datetime import datetime

from aiohttp import ClientSession

from common.domain.schema import Patent
from common.utils.debug import async_timer
from rospatent_scraper.domain.utils import clean_id, remove_xml_tags


@async_timer
async def parse_full_info(id_: str, session: ClientSession) -> Patent:
    id_ = clean_id(id_)
    headers = {'Content-Type': 'application/json'}
    params = {'t': int(datetime.now().timestamp() * 1000)}

    data_row = {
        'pre_tag': '',
        'post_tag': '',
    }

    async with session.post(
        f"https://searchplatform.rospatent.gov.ru/docs/{id_}",
        headers=headers,
        params=params,
        json=data_row,
        verify_ssl=False,
    ) as response:
        full_patent = await response.json(content_type=None)

        id_ = full_patent['id']
        # snippet = full_patent['snippet']
        # title = snippet['title']
        # snipped_description = snippet['description']

        application = full_patent['common']['application']
        application_number = application['number']
        application_filing_date = datetime.strptime(application['filing_date'], "%Y.%m.%d")

        common = full_patent['common']
        publication_date = datetime.strptime(common['publication_date'], "%Y.%m.%d")

        classification = common['classification']
        ipc = classification.get('ipc', None)
        if ipc:
            ipc = [current['fullname'] for current in ipc]

        cpc = classification.get('cpc', None)
        if cpc:
            cpc = [current['fullname'] for current in cpc]

        biblio = full_patent['biblio']
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

        abstract_ru, abstract_en, claims_ru, claims_en, description_ru, description_en = None, None, None, None, None, None

        abstract = full_patent.get('abstract', None)
        if abstract:
            abstract_ru = remove_xml_tags(abstract.get('ru', None))
            abstract_en = remove_xml_tags(abstract.get('en', None))

        claims = full_patent.get('claims', None)
        if claims:
            claims_ru = remove_xml_tags(claims.get('ru', None))
            claims_en = remove_xml_tags(claims.get('en', None))

        description = full_patent.get('description', None)
        if description:
            description_ru = remove_xml_tags(description.get('ru', None))
            description_en = remove_xml_tags(description.get('en', None))

        return Patent(
            id=id_,
            title_ru=title_ru,
            title_en=title_en,
            publication_date=publication_date,
            application_number=application_number,
            application_filing_date=application_filing_date,
            ipc=ipc,
            cpc=cpc,
            # snippet_ru=snipped_description,
            patentees_ru=patentees_ru,
            patentees_en=patentees_en,
            applicants_ru=applicants_ru,
            applicants_en=applicants_en,
            inventors_ru=inventors_ru,
            inventors_en=inventors_en,
            abstract_ru=abstract_ru,
            abstract_en=abstract_en,
            claims_ru=claims_ru,
            claims_en=claims_en,
            description_ru=description_ru,
            description_en=description_en,
        )
