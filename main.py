from flask import Flask, jsonify, request
import os
from functools import lru_cache
import logging

app = Flask(__name__)

# This indicates where is the log file in the local system
LOG_FILE_PATH = r'C:\Users\FatPinguin\PycharmProjects\posteffectAI\hn_logs.tsv'

# Logging for debugging.It is helpful since I can see what have I done and how the program reacted.
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')


# Lazy parser with cache mechanism to prevent unnecessary re-reading of the log file. I configured since initially
# there is 4 different days in the log file we would only need 4 cache spaces to include each day and be efficient
# about it.
@lru_cache(maxsize=4)
def parse_log_file_by_date_prefix(file_path, date_prefix):
    log_entries = []
    try:
        if os.path.exists(file_path):
            logging.info(f"Parsing log file for date prefix: {date_prefix}")
            with open(file_path, 'r') as file:
                for line in file:
                    timestamp, query = line.strip().split('\t')

                    # Check if date_prefix is a full timestamp or just a date
                    if date_prefix is None:
                        log_entries.append({"timestamp": timestamp, "query": query})
                    elif ' ' in date_prefix:  # Full timestamp (YYYY-MM-DD HH:MM:SS)
                        if timestamp == date_prefix:  # Exact match
                            log_entries.append({"timestamp": timestamp, "query": query})
                    else:  # Just a date (YYYY-MM-DD)
                        if timestamp.startswith(date_prefix):  # Starts with date
                            log_entries.append({"timestamp": timestamp, "query": query})
        else:
            logging.error(f"Log file {file_path} does not exist!")
            raise FileNotFoundError(f"Log file {file_path} does not exist!")
    except Exception as e:
        logging.error(f"Error parsing log file: {e}")
    return log_entries


def save_log_entries(file_path, log_entries):
    """Save the updated log entries back to the log file."""
    with open(file_path, 'w') as file:
        for entry in log_entries:
            file.write(f"{entry['timestamp']}\t{entry['query']}\n")


def count_distinct_queries(log_entries):
    """Count distinct queries."""
    distinct_queries = {entry['query'] for entry in log_entries}
    return len(distinct_queries)


@app.route('/queries/count/<date_prefix>', methods=['GET', 'POST', 'DELETE'])
def manage_queries(date_prefix):
    if request.method == 'GET':
        filtered_entries = parse_log_file_by_date_prefix(LOG_FILE_PATH, date_prefix)
        count = count_distinct_queries(filtered_entries)
        return jsonify({"count": count})

    elif request.method == 'POST':
        new_entry = request.json

        # Ensure the JSON has 'timestamp' and 'query'
        if not new_entry or 'timestamp' not in new_entry or 'query' not in new_entry:
            return jsonify({"error": "Invalid request format. 'timestamp' and 'query' are required."}), 400

        # Add the new entry
        with open(LOG_FILE_PATH, 'a') as file:
            file.write(f"{new_entry['timestamp']}\t{new_entry['query']}\n")

        # Clear cache to reflect new additions
        parse_log_file_by_date_prefix.cache_clear()

        return jsonify({"message": "New log entry added!"}), 201

    elif request.method == 'DELETE':

        log_entries = parse_log_file_by_date_prefix(LOG_FILE_PATH, None)
        print(len(log_entries), type(log_entries))
        log_entries_delete = parse_log_file_by_date_prefix(LOG_FILE_PATH, date_prefix)
        print(len(log_entries_delete), type(log_entries_delete))
        # Adjust filtering to support both date and full timestamp (YYYY-MM-DD HH:MM:SS)
        print(date_prefix)
        remaining_entries = []

        print("helloé")
        # Delete only the entry that matches the full timestamp
        remaining_entries = log_entries.copy() #copy yazmadığımızda remaining entries ve log entries aynı pointer gibi davranıyor. copy yazdığımızda ise log entriesin farklı bir yerde kopyasını oluşturup remaininge eşitliyoruz
        for entry in log_entries_delete:
            if entry in log_entries:
                print(entry)
                remaining_entries.remove(entry)

        print(len(remaining_entries))

        print(len(remaining_entries), len(log_entries))
        if len(remaining_entries) == len(log_entries):

            return jsonify({"message": f"No entries found with prefix {date_prefix}"}), 404

        # Save updated log file only if entries were actually removed

        if len(remaining_entries) > 0:
            print("selam")
            save_log_entries(LOG_FILE_PATH, remaining_entries)

        else:

            # If all entries were removed, empty the file

            open(LOG_FILE_PATH, 'w').close()

        # Clear cache to reflect deletion

        parse_log_file_by_date_prefix.cache_clear()

        return jsonify({"message": f"Entries with prefix {date_prefix} deleted!"}), 200


if __name__ == '__main__':

    # By default, host is '127.0.0.1' and port is '5000'.
    host_address = '127.0.0.1'
    port_number = 5000

    app.run(host=host_address, port=port_number, debug=True)
