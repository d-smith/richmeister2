package:
	rm -f replicator.zip
	zip replicator.zip replicator.js

deploy:
	aws s3 cp replicator.zip s3://$(DEPLOY_BUCKET)
	aws s3 cp replicator.yml s3://$(DEPLOY_BUCKET)
