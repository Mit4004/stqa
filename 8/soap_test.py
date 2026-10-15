import http.server
import io
import re
import socketserver
import sys
import threading
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple

SOAP_NAMESPACES = {
    "soap": "http://schemas.xmlsoap.org/soap/envelope/",
    "m": "http://tempuri.org/services",
}

WSDL_CONTENT = """<?xml version="1.0" encoding="utf-8"?>
<wsdl:definitions xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/"
                  xmlns:tns="http://tempuri.org/services"
                  xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/"
                  xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                  targetNamespace="http://tempuri.org/services">
  <wsdl:message name="AddSoapIn">
    <wsdl:part name="intA" type="xsd:int"/>
    <wsdl:part name="intB" type="xsd:int"/>
  </wsdl:message>
  <wsdl:message name="AddSoapOut">
    <wsdl:part name="AddResult" type="xsd:int"/>
  </wsdl:message>
</wsdl:definitions>
"""


class SoapMockHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_soap_response(self, status_code: int, body_xml: str):
        envelope = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:m="http://tempuri.org/services">
  <soap:Body>
    {body_xml}
  </soap:Body>
</soap:Envelope>"""
        response_bytes = envelope.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def send_soap_fault(self, fault_code: str, fault_string: str, detail_msg: Optional[str] = None):
        detail_xml = f"<detail><error>{detail_msg}</error></detail>" if detail_msg else ""
        fault_body = f"""<soap:Fault>
      <faultcode>{fault_code}</faultcode>
      <faultstring>{fault_string}</faultstring>
      {detail_xml}
    </soap:Fault>"""
        self.send_soap_response(status_code=500, body_xml=fault_body)

    def do_GET(self):
        if "?wsdl" in self.path.lower():
            self.send_response(200)
            self.send_header("Content-Type", "text/xml; charset=utf-8")
            self.send_header("Content-Length", str(len(WSDL_CONTENT.encode("utf-8"))))
            self.end_headers()
            self.wfile.write(WSDL_CONTENT.encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h3>SOAP 1.1 Test Web Service Active</h3>")

    def do_POST(self):
        soap_action = self.headers.get("SOAPAction", "").strip('"')
        auth_header = self.headers.get("Authorization", "")

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length).decode("utf-8")

        try:
            root = ET.fromstring(raw_body)
        except ET.ParseError as e:
            self.send_soap_fault("soap:Client.MalformedXML", f"XML Parsing Error: {str(e)}", "Malformed XML payload received")
            return

        if "SecureOperation" in soap_action and auth_header != "Bearer STQA_SOAP_SECURE_TOKEN_2026":
            self.send_soap_fault("soap:Client.AuthenticationFailed", "Invalid or missing security credentials in SOAP Request", "Missing valid Bearer token")
            return

        body_elem = None
        for elem in root.iter():
            if elem.tag.endswith("Body"):
                body_elem = elem
                break

        if body_elem is None or len(body_elem) == 0:
            self.send_soap_fault("soap:Client.MissingBody", "SOAP Body element is missing or empty")
            return

        op_elem = body_elem[0]
        tag_name = op_elem.tag.split("}")[-1] if "}" in op_elem.tag else op_elem.tag

        if tag_name == "Add":
            self.handle_add(op_elem)
        elif tag_name == "Subtract":
            self.handle_subtract(op_elem)
        elif tag_name == "Multiply":
            self.handle_multiply(op_elem)
        elif tag_name == "Divide":
            self.handle_divide(op_elem)
        elif tag_name == "GetAccountBalance":
            self.handle_get_balance(op_elem)
        elif tag_name == "SecureOperation":
            self.send_soap_response(200, "<m:SecureOperationResponse><m:Status>Authorized &amp; Verified</m:Status></m:SecureOperationResponse>")
        else:
            self.send_soap_fault("soap:Client.InvalidAction", f"Operation '{tag_name}' is not supported by this endpoint")

    def handle_add(self, elem):
        a_str, b_str = elem.findtext("{http://tempuri.org/services}intA"), elem.findtext("{http://tempuri.org/services}intB")
        if a_str is None or b_str is None:
            a_str = elem.findtext("intA") if a_str is None else a_str
            b_str = elem.findtext("intB") if b_str is None else b_str

        if a_str is None or b_str is None:
            self.send_soap_fault("soap:Client.MissingParameter", "Missing required parameters 'intA' or 'intB'")
            return
        try:
            a, b = int(a_str), int(b_str)
            res = a + b
            self.send_soap_response(200, f"<m:AddResponse><m:AddResult>{res}</m:AddResult></m:AddResponse>")
        except ValueError:
            self.send_soap_fault("soap:Client.TypeMismatch", "Input parameter could not be parsed as integer", f"Received intA='{a_str}', intB='{b_str}'")

    def handle_subtract(self, elem):
        a_str, b_str = elem.findtext("{http://tempuri.org/services}intA") or elem.findtext("intA"), elem.findtext("{http://tempuri.org/services}intB") or elem.findtext("intB")
        if a_str is None or b_str is None:
            self.send_soap_fault("soap:Client.MissingParameter", "Missing required parameters 'intA' or 'intB'")
            return
        try:
            a, b = int(a_str), int(b_str)
            res = a - b
            self.send_soap_response(200, f"<m:SubtractResponse><m:SubtractResult>{res}</m:SubtractResult></m:SubtractResponse>")
        except ValueError:
            self.send_soap_fault("soap:Client.TypeMismatch", "Input parameter could not be parsed as integer")

    def handle_multiply(self, elem):
        a_str, b_str = elem.findtext("{http://tempuri.org/services}intA") or elem.findtext("intA"), elem.findtext("{http://tempuri.org/services}intB") or elem.findtext("intB")
        if a_str is None or b_str is None:
            self.send_soap_fault("soap:Client.MissingParameter", "Missing required parameters 'intA' or 'intB'")
            return
        try:
            a, b = int(a_str), int(b_str)
            res = a * b
            self.send_soap_response(200, f"<m:MultiplyResponse><m:MultiplyResult>{res}</m:MultiplyResult></m:MultiplyResponse>")
        except ValueError:
            self.send_soap_fault("soap:Client.TypeMismatch", "Input parameter could not be parsed as integer")

    def handle_divide(self, elem):
        a_str, b_str = elem.findtext("{http://tempuri.org/services}intA") or elem.findtext("intA"), elem.findtext("{http://tempuri.org/services}intB") or elem.findtext("intB")
        if a_str is None or b_str is None:
            self.send_soap_fault("soap:Client.MissingParameter", "Missing required parameters 'intA' or 'intB'")
            return
        try:
            a, b = int(a_str), int(b_str)
            if b == 0:
                self.send_soap_fault("soap:Server.DivisionByZero", "Cannot divide by zero: ArithmeticException", "Attempted division by zero in Divide operation")
                return
            res = a / b
            res_val = int(res) if res.is_integer() else round(res, 4)
            self.send_soap_response(200, f"<m:DivideResponse><m:DivideResult>{res_val}</m:DivideResult></m:DivideResponse>")
        except ValueError:
            self.send_soap_fault("soap:Client.TypeMismatch", "Input parameter could not be parsed as integer")

    def handle_get_balance(self, elem):
        acc = elem.findtext("{http://tempuri.org/services}accountNumber") or elem.findtext("accountNumber")
        if not acc:
            self.send_soap_fault("soap:Client.MissingParameter", "Missing 'accountNumber' parameter")
            return
        if acc == "ACC-1001":
            self.send_soap_response(200, """<m:GetAccountBalanceResponse>
  <m:AccountDetails>
    <m:AccountNumber>ACC-1001</m:AccountNumber>
    <m:AccountHolder>Rahul Sharma</m:AccountHolder>
    <m:Balance>54250.75</m:Balance>
    <m:Currency>INR</m:Currency>
    <m:Status>Active</m:Status>
  </m:AccountDetails>
</m:GetAccountBalanceResponse>""")
        else:
            self.send_soap_fault("soap:Client.AccountNotFound", f"Account '{acc}' does not exist in the banking records", f"Queried account: {acc}")


class SoapServerThread(threading.Thread):
    def __init__(self, host="127.0.0.1", port=8088):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.server = socketserver.TCPServer((self.host, self.port), SoapMockHandler)

    def run(self):
        self.server.serve_forever()

    def shutdown_server(self):
        self.server.shutdown()
        self.server.server_close()


class SoapTestClient:
    def __init__(self, endpoint_url: str):
        self.endpoint_url = endpoint_url

    def send_soap_request(
        self,
        soap_action: str,
        xml_payload: str,
        custom_headers: Optional[Dict[str, str]] = None,
        timeout: float = 5.0
    ) -> Tuple[int, str, float]:
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": f'"{soap_action}"',
        }
        if custom_headers:
            headers.update(custom_headers)

        req = urllib.request.Request(
            url=self.endpoint_url,
            data=xml_payload.encode("utf-8"),
            headers=headers,
            method="POST"
        )

        start_time = time.perf_counter()
        status_code = 0
        response_text = ""

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code = response.status
                response_text = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as http_err:
            status_code = http_err.code
            response_text = http_err.read().decode("utf-8", errors="replace")
        except Exception as err:
            status_code = -1
            response_text = f"<error>{str(err)}</error>"

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return status_code, response_text, elapsed_ms

    @staticmethod
    def parse_soap_fault(response_xml: str) -> Dict[str, str]:
        fault_info = {"faultcode": "", "faultstring": "", "detail": ""}
        try:
            root = ET.fromstring(response_xml)
            for elem in root.iter():
                tag_lower = elem.tag.split("}")[-1].lower()
                if tag_lower == "faultcode":
                    fault_info["faultcode"] = elem.text or ""
                elif tag_lower == "faultstring":
                    fault_info["faultstring"] = elem.text or ""
                elif tag_lower == "detail" or tag_lower == "error":
                    fault_info["detail"] = "".join(elem.itertext()).strip()
        except ET.ParseError:
            pass
        return fault_info

    @staticmethod
    def extract_element_value(response_xml: str, tag_name: str) -> Optional[str]:
        try:
            root = ET.fromstring(response_xml)
            for elem in root.iter():
                if elem.tag.split("}")[-1] == tag_name:
                    return elem.text
        except ET.ParseError:
            return None
        return None


class SoapTestSuite:
    def __init__(self, endpoint_url: str):
        self.client = SoapTestClient(endpoint_url)
        self.results: List[Dict] = []

    def log_test_header(self, test_id: str, title: str, category: str):
        print(f"\n[{test_id}] {category.upper()}: {title}")
        print("-" * 75)

    def record_result(self, test_id: str, name: str, category: str, passed: bool, message: str, elapsed_ms: float):
        status_str = "PASS [OK]" if passed else "FAIL [X]"
        self.results.append({
            "id": test_id,
            "name": name,
            "category": category,
            "passed": passed,
            "message": message,
            "latency": elapsed_ms
        })
        print(f"  Result : {status_str} (Latency: {elapsed_ms:.2f} ms)")
        print(f"  Notes  : {message}")

    def test_addition(self):
        test_id = "TC-FUNC-01"
        self.log_test_header(test_id, "SOAP Add Operation (45 + 55 = 100)", "Functionality")
        payload = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:m="http://tempuri.org/services">
  <soap:Body>
    <m:Add>
      <m:intA>45</m:intA>
      <m:intB>55</m:intB>
    </m:Add>
  </soap:Body>
</soap:Envelope>"""
        status, resp, elapsed = self.client.send_soap_request("Add", payload)
        val = self.client.extract_element_value(resp, "AddResult")
        passed = (status == 200 and val == "100")
        self.record_result(test_id, "Addition Operation", "Functionality", passed,
                           f"HTTP {status}, AddResult: {val} (Expected 100)", elapsed)

    def test_subtraction(self):
        test_id = "TC-FUNC-02"
        self.log_test_header(test_id, "SOAP Subtract Operation (120 - 45 = 75)", "Functionality")
        payload = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:m="http://tempuri.org/services">
  <soap:Body>
    <m:Subtract>
      <m:intA>120</m:intA>
      <m:intB>45</m:intB>
    </m:Subtract>
  </soap:Body>
</soap:Envelope>"""
        status, resp, elapsed = self.client.send_soap_request("Subtract", payload)
        val = self.client.extract_element_value(resp, "SubtractResult")
        passed = (status == 200 and val == "75")
        self.record_result(test_id, "Subtraction Operation", "Functionality", passed,
                           f"HTTP {status}, SubtractResult: {val} (Expected 75)", elapsed)

    def test_multiplication(self):
        test_id = "TC-FUNC-03"
        self.log_test_header(test_id, "SOAP Multiply Operation (14 * 8 = 112)", "Functionality")
        payload = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:m="http://tempuri.org/services">
  <soap:Body>
    <m:Multiply>
      <m:intA>14</m:intA>
      <m:intB>8</m:intB>
    </m:Multiply>
  </soap:Body>
</soap:Envelope>"""
        status, resp, elapsed = self.client.send_soap_request("Multiply", payload)
        val = self.client.extract_element_value(resp, "MultiplyResult")
        passed = (status == 200 and val == "112")
        self.record_result(test_id, "Multiplication Operation", "Functionality", passed,
                           f"HTTP {status}, MultiplyResult: {val} (Expected 112)", elapsed)

    def test_division(self):
        test_id = "TC-FUNC-04"
        self.log_test_header(test_id, "SOAP Divide Operation (225 / 15 = 15)", "Functionality")
        payload = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:m="http://tempuri.org/services">
  <soap:Body>
    <m:Divide>
      <m:intA>225</m:intA>
      <m:intB>15</m:intB>
    </m:Divide>
  </soap:Body>
</soap:Envelope>"""
        status, resp, elapsed = self.client.send_soap_request("Divide", payload)
        val = self.client.extract_element_value(resp, "DivideResult")
        passed = (status == 200 and val == "15")
        self.record_result(test_id, "Division Operation", "Functionality", passed,
                           f"HTTP {status}, DivideResult: {val} (Expected 15)", elapsed)

    def test_account_query(self):
        test_id = "TC-FUNC-05"
        self.log_test_header(test_id, "SOAP Complex Query - Account Balance Verification", "Functionality")
        payload = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:m="http://tempuri.org/services">
  <soap:Body>
    <m:GetAccountBalance>
      <m:accountNumber>ACC-1001</m:accountNumber>
    </m:GetAccountBalance>
  </soap:Body>
</soap:Envelope>"""
        status, resp, elapsed = self.client.send_soap_request("GetAccountBalance", payload)
        holder = self.client.extract_element_value(resp, "AccountHolder")
        balance = self.client.extract_element_value(resp, "Balance")
        passed = (status == 200 and holder == "Rahul Sharma" and balance == "54250.75")
        self.record_result(test_id, "Account Balance Query", "Functionality", passed,
                           f"HTTP {status}, Holder: '{holder}', Balance: {balance} INR", elapsed)

    def test_fault_divide_by_zero(self):
        test_id = "TC-FAULT-01"
        self.log_test_header(test_id, "Fault Check: Arithmetic Division by Zero", "Fault Checking")
        payload = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:m="http://tempuri.org/services">
  <soap:Body>
    <m:Divide>
      <m:intA>50</m:intA>
      <m:intB>0</m:intB>
    </m:Divide>
  </soap:Body>
</soap:Envelope>"""
        status, resp, elapsed = self.client.send_soap_request("Divide", payload)
        fault = self.client.parse_soap_fault(resp)
        passed = (status == 500 and "DivisionByZero" in fault["faultcode"])
        self.record_result(test_id, "Divide by Zero Fault", "Fault Checking", passed,
                           f"HTTP {status} -> FaultCode: '{fault['faultcode']}', FaultString: '{fault['faultstring']}'", elapsed)

    def test_fault_type_mismatch(self):
        test_id = "TC-FAULT-02"
        self.log_test_header(test_id, "Fault Check: Schema Type Mismatch (Passing string 'invalid_num' to int)", "Fault Checking")
        payload = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:m="http://tempuri.org/services">
  <soap:Body>
    <m:Add>
      <m:intA>100</m:intA>
      <m:intB>invalid_text</m:intB>
    </m:Add>
  </soap:Body>
</soap:Envelope>"""
        status, resp, elapsed = self.client.send_soap_request("Add", payload)
        fault = self.client.parse_soap_fault(resp)
        passed = (status == 500 and "TypeMismatch" in fault["faultcode"])
        self.record_result(test_id, "Type Mismatch Fault", "Fault Checking", passed,
                           f"HTTP {status} -> FaultCode: '{fault['faultcode']}', String: '{fault['faultstring']}'", elapsed)

    def test_fault_missing_parameter(self):
        test_id = "TC-FAULT-03"
        self.log_test_header(test_id, "Fault Check: Missing Mandatory Parameter Tag (Missing intB)", "Fault Checking")
        payload = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:m="http://tempuri.org/services">
  <soap:Body>
    <m:Add>
      <m:intA>100</m:intA>
    </m:Add>
  </soap:Body>
</soap:Envelope>"""
        status, resp, elapsed = self.client.send_soap_request("Add", payload)
        fault = self.client.parse_soap_fault(resp)
        passed = (status == 500 and "MissingParameter" in fault["faultcode"])
        self.record_result(test_id, "Missing Parameter Fault", "Fault Checking", passed,
                           f"HTTP {status} -> FaultCode: '{fault['faultcode']}', String: '{fault['faultstring']}'", elapsed)

    def test_fault_malformed_xml(self):
        test_id = "TC-FAULT-04"
        self.log_test_header(test_id, "Fault Check: Malformed XML Envelope (Unclosed Tag)", "Fault Checking")
        payload = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <m:Add>
      <m:intA>10</m:intA>
      <m:intB>20
  </soap:Body>
</soap:Envelope>"""
        status, resp, elapsed = self.client.send_soap_request("Add", payload)
        fault = self.client.parse_soap_fault(resp)
        passed = (status == 500 and "MalformedXML" in fault["faultcode"])
        self.record_result(test_id, "Malformed XML Fault", "Fault Checking", passed,
                           f"HTTP {status} -> FaultCode: '{fault['faultcode']}', String: '{fault['faultstring']}'", elapsed)

    def test_fault_invalid_operation(self):
        test_id = "TC-FAULT-05"
        self.log_test_header(test_id, "Fault Check: Invalid / Unsupported Operation Call", "Fault Checking")
        payload = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:m="http://tempuri.org/services">
  <soap:Body>
    <m:UnknownServiceAction>
      <m:query>test</m:query>
    </m:UnknownServiceAction>
  </soap:Body>
</soap:Envelope>"""
        status, resp, elapsed = self.client.send_soap_request("UnknownServiceAction", payload)
        fault = self.client.parse_soap_fault(resp)
        passed = (status == 500 and "InvalidAction" in fault["faultcode"])
        self.record_result(test_id, "Invalid Action Fault", "Fault Checking", passed,
                           f"HTTP {status} -> FaultCode: '{fault['faultcode']}', String: '{fault['faultstring']}'", elapsed)

    def test_fault_unauthorized_access(self):
        test_id = "TC-FAULT-06"
        self.log_test_header(test_id, "Fault Check: Unauthorized Access to Secure Operation", "Fault Checking")
        payload = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:m="http://tempuri.org/services">
  <soap:Body>
    <m:SecureOperation />
  </soap:Body>
</soap:Envelope>"""
        status, resp, elapsed = self.client.send_soap_request("SecureOperation", payload, custom_headers={"Authorization": "Bearer BAD_KEY"})
        fault = self.client.parse_soap_fault(resp)
        passed = (status == 500 and "AuthenticationFailed" in fault["faultcode"])
        self.record_result(test_id, "Unauthorized Access Fault", "Fault Checking", passed,
                           f"HTTP {status} -> FaultCode: '{fault['faultcode']}', String: '{fault['faultstring']}'", elapsed)

    def run_all(self):
        print("\n" + "=" * 75)
        print("          SOAP WEB SERVICES FUNCTIONAL & FAULT TEST SUITE")
        print("=" * 75)
        print(f" Target Endpoint : {self.client.endpoint_url}")
        print(" Protocol        : SOAP 1.1 over HTTP (POST)")
        print(" Test Execution  : Automated Assertions & Fault Payload Inspection")
        print("=" * 75)

        self.test_addition()
        self.test_subtraction()
        self.test_multiplication()
        self.test_division()
        self.test_account_query()

        self.test_fault_divide_by_zero()
        self.test_fault_type_mismatch()
        self.test_fault_missing_parameter()
        self.test_fault_malformed_xml()
        self.test_fault_invalid_operation()
        self.test_fault_unauthorized_access()

        self.display_summary()

    def display_summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        pass_rate = (passed / total) * 100 if total > 0 else 0

        print("\n" + "=" * 75)
        print("                        TEST EXECUTION SUMMARY")
        print("=" * 75)
        print(f"{'Test ID':<13} | {'Category':<16} | {'Test Description':<25} | {'Result':<8} | {'Latency':<8}")
        print("-" * 75)
        for r in self.results:
            res_str = "PASS" if r["passed"] else "FAIL"
            print(f"{r['id']:<13} | {r['category']:<16} | {r['name']:<25} | {res_str:<8} | {r['latency']:.1f}ms")
        print("=" * 75)
        print(f" Total Tests Run : {total}")
        print(f" Passed          : {passed}")
        print(f" Failed          : {failed}")
        print(f" Pass Percentage : {pass_rate:.2f}%")
        print("=" * 75 + "\n")


def main():
    port = 8088
    server_thread = SoapServerThread(port=port)
    server_thread.start()
    time.sleep(0.3)

    endpoint = f"http://127.0.0.1:{port}/SoapCalculatorService"

    try:
        suite = SoapTestSuite(endpoint)
        suite.run_all()
    finally:
        server_thread.shutdown_server()


if __name__ == "__main__":
    main()
