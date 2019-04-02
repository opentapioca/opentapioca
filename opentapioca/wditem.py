
class WikidataItemDocument(object):
    def __init__(self, json):
        self.json = json

    def get(self, field, default_value=None):
        return self.json.get(field, default_value)
    
    def __repr__(self):
        return '<WikidataItemDocument {}>'.format(self.json.get('id') or '(unknown qid)')

    def __iter__(self):
        return self.json.__iter__()

    def get_outgoing_edges(self, include_p31=True, numeric=True):
        """
        Given a JSON representation of an item,
        return the list of outgoing edges,
        as integers.
        """
        claims = self.get('claims', {})
        final_key = 'numeric-id' if numeric else 'id'
        res = []
        for pid, pclaims in claims.items():
            if pid == 'P31' and not include_p31:
                continue
            for c in pclaims:
                try:
                    res.append(c['mainsnak']['datavalue']['value'][final_key])
                except (KeyError, TypeError):
                    pass

                qualifiers = c.get('qualifiers', {})
                for pid, qs in qualifiers.items():
                    for q in qs:
                        try:
                            res.append(q['datavalue']['value'][final_key])
                        except (KeyError, TypeError):
                            pass
        return res

    def get_nb_statements(self):
        """
        Number of claims on the item
        """
        nb_claims = 0
        for pclaims in self.get('claims', {}).values():
            nb_claims += len(pclaims)
        return nb_claims

    def get_nb_sitelinks(self):
        """
        Number of sitelinks on this item
        """
        return len(self.get('sitelinks', []))

    def get_types(self, pid='P31'):
        """
        Values of P31 claims
        """
        type_claims = self.get('claims', {}).get(pid, [])
        type_qids = [
            claim.get('mainsnak', {}).get('datavalue', {}).get('value', {}).get('id')
            for claim in type_claims
        ]
        valid_type_qids = [ qid for qid in type_qids if qid ]
        return valid_type_qids

    def get_default_label(self, language):
        """
        English label if provided, otherwise any other label
        """
        labels = self.get('labels', {})
        preferred_label = labels.get(language, {}).get('value')
        if preferred_label:
            return preferred_label
        enlabel = labels.get('en', {}).get('value')
        if enlabel:
            return enlabel
        for other_lang in labels:
            return labels.get(other_lang, {}).get('value')
        return None

    def get_all_terms(self):
        """
        All labels and aliases in all languages, made unique
        """
        all_labels = {
            label['value']
            for label in self.get('labels', {}).values()
        }
        for aliases in self.get('aliases', {}).values():
            all_labels |= { alias['value'] for alias in aliases }
        return all_labels

    def get_aliases(self, lang):
        aliases = [
            alias['value']
            for alias in self.get('aliases', {}).get(lang, [])
        ]
        return aliases

    def get_identifiers(self, pid):
        # Fetch GRID
        id_claims = self.get('claims', {}).get(pid, [])
        ids = [
            claim.get('mainsnak', {}).get('datavalue', {}).get('value', {})
            for claim in id_claims
        ]
        valid_ids = [ id for id in ids if id ]
        return valid_ids


