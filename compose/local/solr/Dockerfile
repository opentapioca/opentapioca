FROM solr:7.7.3

COPY ./configsets /configsets

COPY --chown=solr:solr ./compose/local/solr/entrypoint /entrypoint
RUN chmod +x /entrypoint

ENTRYPOINT ["/entrypoint"]