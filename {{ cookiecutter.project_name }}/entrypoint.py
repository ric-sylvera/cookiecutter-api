#!/usr/bin/env python
import logging
import os

import click
import uvicorn

SSL_CERT_FILE = "/rds-cert-bundle.pem"


@click.command()
@click.option(
    "--local", is_flag=True, default=False, help="Enable local mode, with auto-reload."
)
def run(local):
    port = int(os.getenv("PORT", "8080"))
    log_level = os.getenv("LOG_LEVEL", "info")
    logging.debug(f"Local run:\t{local}")

    if not local:
        logging.info("Check AWS RDS certificate exists...")
        if not os.path.isfile(SSL_CERT_FILE):
            raise Exception(f"AWS RDS certificate does not exist at `{SSL_CERT_FILE}`")

        logging.info("Set SSL environment variables for connection to database.")
        os.environ["PGSSLMODE"] = "verify-full"
        os.environ["PGSSLROOTCERT"] = SSL_CERT_FILE

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=local,
        log_level=log_level,
        log_config="logconfig.yml",
    )


if __name__ == "__main__":
    run()
