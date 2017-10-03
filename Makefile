package:
	rm -rf replicator.zip
	zip replicator.zip Replicator.py

deploy:
	aws s3 cp replicator.zip s3://$(DEPLOY_BUCKET)
	aws s3 cp replicator.yml s3://$(DEPLOY_BUCKET)
