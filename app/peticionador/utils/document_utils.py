import logging

logger = logging.getLogger(__name__)


def replace_placeholders_in_doc(doc_id, replacements, docs_service):
    """
    Substitui placeholders em um documento do Google Docs.
    """
    try:
        requests = [
            {
                "replaceAllText": {
                    "containsText": {"text": f"{{{{{key}}}}}", "matchCase": "true"},
                    "replaceText": str(value),
                }
            }
            for key, value in replacements.items()
        ]

        if requests:
            docs_service.documents().batchUpdate(
                documentId=doc_id, body={"requests": requests}
            ).execute()
        return True
    except Exception as e:
        logger.error(f"Erro ao substituir placeholders no doc {doc_id}: {e}", exc_info=True)
        return False 