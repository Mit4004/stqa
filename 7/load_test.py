
import time
import urllib.request
import urllib.error
import concurrent.futures
import statistics

TARGET_URL = "https://www.saucedemo.com/" 
CONCURRENT_USERS = 20   
REQUESTS_PER_USER = 5    
TIMEOUT_SECONDS = 10    


def send_request(user_id, request_num):

    req = urllib.request.Request(
        TARGET_URL,
        headers={"User-Agent": f"LoadTester-User-{user_id}"}
    )

    start_time = time.time()
    status_code = None
    success = False
    error_msg = ""

    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            status_code = response.getcode()
            response.read()  
            success = (200 <= status_code < 400)
    except urllib.error.HTTPError as e:
        status_code = e.code
        error_msg = f"HTTP Error {e.code}"
    except urllib.error.URLError as e:
        status_code = "ERR"
        error_msg = str(e.reason)
    except Exception as e:
        status_code = "ERR"
        error_msg = str(e)

    end_time = time.time()
    response_time_ms = (end_time - start_time) * 1000 

    return {
        "user_id": user_id,
        "request_num": request_num,
        "status_code": status_code,
        "response_time_ms": response_time_ms,
        "success": success,
        "error_msg": error_msg,
    }


def run_load_test():
    total_requests = CONCURRENT_USERS * REQUESTS_PER_USER
    print("=" * 65)
    print("           WEB APPLICATION LOAD TESTING REPORT")
    print("=" * 65)
    print(f" Target Endpoint    : {TARGET_URL}")
    print(f" Concurrent Users   : {CONCURRENT_USERS}")
    print(f" Requests Per User  : {REQUESTS_PER_USER}")
    print(f" Total Requests     : {total_requests}")
    print("=" * 65)
    print("\n[+] Starting load test execution...\n")

    results = []
    overall_start_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
        futures = []
        for user_id in range(1, CONCURRENT_USERS + 1):
            for req_num in range(1, REQUESTS_PER_USER + 1):
                futures.append(executor.submit(send_request, user_id, req_num))

        completed_count = 0
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            results.append(res)
            completed_count += 1
            status_display = "OK" if res["success"] else "FAIL"
            print(f"  [Request {completed_count:3d}/{total_requests}] User {res['user_id']:02d} -> "
                  f"Status: {res['status_code']} | Latency: {res['response_time_ms']:7.2f} ms | [{status_display}]")

    overall_end_time = time.time()
    total_duration_sec = overall_end_time - overall_start_time

    response_times = [r["response_time_ms"] for r in results]
    success_count = sum(1 for r in results if r["success"])
    fail_count = total_requests - success_count
    error_rate = (fail_count / total_requests) * 100

    min_time = min(response_times) if response_times else 0
    max_time = max(response_times) if response_times else 0
    avg_time = statistics.mean(response_times) if response_times else 0
    median_time = statistics.median(response_times) if response_times else 0
    p90_time = statistics.quantiles(response_times, n=10)[8] if len(response_times) >= 10 else max_time
    p95_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max_time
    throughput = total_requests / total_duration_sec if total_duration_sec > 0 else 0

    print("\n" + "=" * 65)
    print("                 PERFORMANCE SUMMARY")
    print("=" * 65)
    print(f" Total Execution Time  : {total_duration_sec:.2f} seconds")
    print(f" Total Samples         : {total_requests}")
    print(f" Successful Requests   : {success_count}")
    print(f" Failed Requests       : {fail_count} ({error_rate:.2f}%)")
    print(f" Throughput            : {throughput:.2f} requests/sec")
    print("-" * 65)
    print(" Response Time Metrics (Latency):")
    print(f"   • Min Response Time : {min_time:.2f} ms")
    print(f"   • Max Response Time : {max_time:.2f} ms")
    print(f"   • Avg Response Time : {avg_time:.2f} ms")
    print(f"   • Median Response   : {median_time:.2f} ms")
    print(f"   • 90th Percentile   : {p90_time:.2f} ms")
    print(f"   • 95th Percentile   : {p95_time:.2f} ms")
    print("=" * 65)


if __name__ == "__main__":
    run_load_test()
