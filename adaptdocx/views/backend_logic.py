from ..models import AdaptdocxClient, AdaptdocxFormSubcategory


def insert_record_matter(model, data):
    try:
        data['offering'] = AdaptdocxFormSubcategory.objects.get(id=data['offering'])
        data['client'] = AdaptdocxClient.objects.get(client_id=data['client'])
        record = model.objects.create(**data)
        record.save()
        return record
    except Exception as e:
        raise e


def insert_record_phone(model, data):
    try:
        if data['is_primary']:
            try:
                obj = model.objects.get(client_id=data['client_id'])
                obj.is_primary = False
                obj.save()
            except:
                pass
        data['client_id'] = AdaptdocxClient.objects.get(client_id=data['client_id'])

        record = model.objects.create(**data)
        record.save()
        return record
    except Exception as e:
        raise e

