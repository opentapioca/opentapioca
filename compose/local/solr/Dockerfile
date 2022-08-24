FROM solr:9.0.0

COPY ./configsets /configsets

COPY --chown=solr:solr ./compose/local/solr/entrypoint /entrypoint
RUN chmod +x /entrypoint

ENTRYPOINT ["/entrypoint"]