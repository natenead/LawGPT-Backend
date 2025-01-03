FROM python:3.10
EXPOSE 5002
# Update the package list and install the ODBC library
# Install the ODBC driver for SQL Server
RUN apt-get update && \
    apt-get install -y gnupg unixodbc-dev && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 && \
    rm -rf /var/lib/apt/lists/*

# # Update ODBC configuration files
# RUN echo "[ODBC Driver 17 for SQL Server]" > /etc/odbcinst.ini && \
#     echo "Description=Microsoft ODBC Driver 17 for SQL Server" >> /etc/odbcinst.ini && \
#     echo "Driver=/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.9.so.1.1" >> /etc/odbcinst.ini && \
#     echo "UsageCount=1" >> /etc/odbcinst.ini


# RUN apt-get install curl
# RUN apt-get install apt-transport-https
# RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
# RUN curl https://packages.microsoft.com/config/ubuntu/16.04/prod.list | tee /etc/apt/sources.list.d/msprod.list

# RUN apt-get install multiarch-support
# RUN apt-get install -y mssql-tools unixodbc-dev


WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

