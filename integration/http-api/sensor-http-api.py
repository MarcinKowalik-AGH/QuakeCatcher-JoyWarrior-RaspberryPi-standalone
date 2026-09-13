#!/usr/bin/python3
# Raspberry Pi Radioactive@Home + Quake-Catcher HTTP API
# Author: Marcin Kowalik
# E-mail: mkowalik@agh.edu.pl
# SPDX-License-Identifier: MIT

import csv, glob, io, json, os, socket
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = "0.0.0.0"
PORT = 80
RADIOACTIVE_CSV = "/opt/radioactive/measurements.csv"
QCN_LIVE = "/run/qcn/latest.json"
QCN_EVENTS = "/var/lib/qcn/events"

def utcnow():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def read_radioactive():
    result={"available":False}
    try:
        with open(RADIOACTIVE_CSV,"r",newline="") as f: rows=list(csv.DictReader(f))
        if not rows: return result
        row=rows[-1]
        return {"available":True,"timestamp_utc":row.get("timestamp_utc"),"timer_ms":int(row["timer_ms"]) if row.get("timer_ms") else None,"counter":int(row["counter"]) if row.get("counter") else None,"delta_ms":int(row["delta_ms"]) if row.get("delta_ms") else None,"delta_counts":int(row["delta_counts"]) if row.get("delta_counts") else None,"cpm":float(row["cpm"]) if row.get("cpm") else None,"dose_uSv_h_est":float(row["dose_uSv_h_est"]) if row.get("dose_uSv_h_est") else None,"revision":int(row["revision"]) if row.get("revision") else None,"device_id":int(row["device_id"]) if row.get("device_id") else None,"status":row.get("status")}
    except Exception as e:
        result["error"]=str(e); return result

def read_qcn():
    result={"available":False}
    try:
        with open(QCN_LIVE,"r") as f: data=json.load(f)
        data["available"]=True; return data
    except Exception as e:
        result["error"]=str(e); return result

def read_latest_event():
    result={"available":False}
    try:
        files=glob.glob(os.path.join(QCN_EVENTS,"event-*.json"))
        if not files: return result
        latest=max(files,key=os.path.getmtime)
        with open(latest,"r") as f: data=json.load(f)
        data["available"]=True; data["metadata_file"]=os.path.basename(latest); return data
    except Exception as e:
        result["error"]=str(e); return result

def combined():
    return {"generated_utc":utcnow(),"hostname":socket.gethostname(),"author":"Marcin Kowalik","email":"mkowalik@agh.edu.pl","radioactive":read_radioactive(),"quakecatcher":read_qcn()}

def dict_to_csv(data):
    out=io.StringIO(); fields=list(data.keys()); writer=csv.DictWriter(out,fieldnames=fields); writer.writeheader(); writer.writerow(data); return out.getvalue()

def sensors_csv():
    rad=read_radioactive(); qcn=read_qcn()
    return dict_to_csv({"generated_utc":utcnow(),"radioactive_timestamp_utc":rad.get("timestamp_utc"),"radioactive_cpm":rad.get("cpm"),"radioactive_uSv_h":rad.get("dose_uSv_h_est"),"radioactive_counter":rad.get("counter"),"radioactive_status":rad.get("status"),"qcn_timestamp_utc":qcn.get("timestamp_utc"),"qcn_x":qcn.get("x"),"qcn_y":qcn.get("y"),"qcn_z":qcn.get("z"),"qcn_residual":qcn.get("residual_vector_counts"),"qcn_event_active":qcn.get("event_active"),"qcn_trigger":qcn.get("trigger_threshold_counts")})

class Handler(BaseHTTPRequestHandler):
    server_version="MarcinKowalik-SensorAPI/1.0"
    def log_message(self,fmt,*args): pass
    def send_common_headers(self,content_type):
        self.send_header("Content-Type",content_type); self.send_header("Cache-Control","no-store, no-cache, must-revalidate"); self.send_header("Access-Control-Allow-Origin","*"); self.send_header("X-Author","Marcin Kowalik")
    def send_json(self,obj,status=200):
        body=(json.dumps(obj,ensure_ascii=False,indent=2)+"\n").encode("utf-8"); self.send_response(status); self.send_common_headers("application/json; charset=utf-8"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
    def send_text(self,text,content_type):
        body=text.encode("utf-8"); self.send_response(200); self.send_common_headers(content_type); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        path=self.path.split("?",1)[0]
        if path=="/": self.send_text("Marcin Kowalik sensor station\n\nRadioactive@Home + Quake-Catcher\n\nAuthor: Marcin Kowalik\nE-mail: mkowalik@agh.edu.pl\n\nEndpoints:\n\n/sensors.json\n/sensors.csv\n\n/radioactive.json\n/radioactive.csv\n\n/qcn.json\n/qcn.csv\n\n/qcn/event/latest.json\n","text/plain; charset=utf-8"); return
        if path=="/sensors.json": self.send_json(combined()); return
        if path=="/sensors.csv": self.send_text(sensors_csv(),"text/csv; charset=utf-8"); return
        if path=="/radioactive.json": self.send_json(read_radioactive()); return
        if path=="/radioactive.csv": self.send_text(dict_to_csv(read_radioactive()),"text/csv; charset=utf-8"); return
        if path=="/qcn.json": self.send_json(read_qcn()); return
        if path=="/qcn.csv": self.send_text(dict_to_csv(read_qcn()),"text/csv; charset=utf-8"); return
        if path=="/qcn/event/latest.json": self.send_json(read_latest_event()); return
        self.send_json({"error":"not found","path":path},status=404)

if __name__=="__main__":
    server=ThreadingHTTPServer((HOST,PORT),Handler); print(f"Sensor HTTP API listening on {HOST}:{PORT}",flush=True); server.serve_forever()
