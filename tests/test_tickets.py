"""Design request tickets (scripts/tickets.py): the request form, the estimate, the quote package, the mail loop."""
import json

import pytest

from scripts import tickets as T

REQUEST_MAIL = (
    "Your name: Ana Ruiz\nYour e-mail: ana@example.org\nWhat do you need: A corner bracket\n"
    "What is it for: Holding a 12 mm plywood shelf to a stud.\nSizes it must fit (mm): Arms ~40 long, M4 screws.\n"
    "Extra line that continues the sizes.\nHow many: 4\nMaterial and colour: PETG, black\n"
)
REPORT = {"project": "demo", "build_id": "b1", "built_at": "2026-09-10 10:00", "docstring": "A demo part.",
          "params": [{"name": "ARM_LEN", "value": 40.0, "comment": "mm", "derived": False}],
          "parts": {"bracket": {"metrics": {"bbox_size": [40.0, 40.0, 20.0], "volume": 5723.6, "surface_area": 3974.8},
                                "printability": {"wall_min_mm": 4.0}, "print_mode": "normal"}},
          "plate": {"extent": [40, 40, 20], "fits_bed": True}, "fit_checks": {}, "components": []}
PRICING = json.loads((T.PRICING_JSON).read_text(encoding="utf-8"))


def test_request_text_round_trips_through_the_parser():
    fields = T.parse_request_text(REQUEST_MAIL)
    assert fields["name"] == "Ana Ruiz" and fields["email"] == "ana@example.org" and fields["quantity"] == "4"
    assert fields["dimensions"].startswith("Arms ~40 long") and "continues the sizes" in fields["dimensions"]
    assert T.parse_request_text(T.request_text(fields)) == fields
    assert T.missing_fields(fields) == []
    assert T.missing_fields({"name": "x"}) == ["Your e-mail", "What do you need", "What is it for", "Sizes it must fit (mm)"]


def test_estimate_scales_with_quantity_and_material():
    one = T.estimate(REPORT, "PLA", 1, PRICING)
    four = T.estimate(REPORT, "PLA", 4, PRICING)
    petg = T.estimate(REPORT, "PETG", 1, PRICING)
    assert 0 < one["mass_g"] < REPORT["parts"]["bracket"]["metrics"]["volume"] / 1000 * 1.24   # lighter than solid
    assert four["mass_g"] == pytest.approx(one["mass_g"] * 4, abs=0.2) and four["total"] > one["total"]
    assert four["per_unit"] < one["total"] and petg["mass_g"] > one["mass_g"]
    assert one["total"] >= PRICING["min_charge"] and one["lead_days"] >= PRICING["queue_days"] + 1
    assert one["rates"]["material"]["cost_per_kg"] == PRICING["materials"]["PLA"]["cost_per_kg"]
    md = T.measurements_md(REPORT, one)
    assert "| bracket | 40 x 40 x 20 |" in md and "| ARM_LEN | 40.0 | mm |" in md


def test_reply_classification():
    assert T.classify_reply("CONFIRM\n\nOn Wed wrote:\n> quoted stuff with the word cancel") == "approved"
    assert T.classify_reply("Looks good but could you make the arms 50 mm?") == "changes"
    assert T.classify_reply("The arms should be 50 mm and the holes M4.") == "changes"
    assert T.classify_reply("no thanks, found one in a shop") == "declined"
    assert T.strip_quoted("yes please\n\nOn Wed, Sep 10 wrote:\n> old") == "yes please"


def test_ticket_lifecycle_and_ingest(tmp_path, monkeypatch):
    monkeypatch.setattr(T, "TICKETS_DIR", tmp_path / "tickets")
    t = T.new_ticket(name="Ana Ruiz", mail="ana@example.org", title="A corner bracket", fields=T.parse_request_text(REQUEST_MAIL), text=REQUEST_MAIL)
    assert t["id"] == "REQ-0001" and t["status"] == "new" and t["messages"][0]["kind"] == "request"
    T.save_ticket(t)
    assert T.next_id() == "REQ-0002"
    # a quote package from a synthetic report, then "sent" through an external client
    monkeypatch.setattr(T, "list_projects", lambda: ["demo"])
    monkeypatch.setattr(T, "MODELS_DIR", tmp_path / "models")
    (tmp_path / "models" / "demo" / "exports" / "renders").mkdir(parents=True)
    (tmp_path / "models" / "demo" / "exports" / "build_report.json").write_text(json.dumps(REPORT), encoding="utf-8")
    (tmp_path / "models" / "demo" / "exports" / "view.html").write_text("<p>viewer</p>", encoding="utf-8")
    q = T.make_quote(t, "demo", note="Went with the proven bracket.")
    assert q["rev"] == 1 and q["material"] == "PETG" and q["qty"] == 4 and q["subject"].startswith("[REQ-0001] Quote r1")
    assert "CONFIRM" in q["email_text"] and "Went with the proven bracket." in q["email_html"] and "ARM_LEN" in q["email_html"]
    qd = T.quote_dir(t, 1)
    assert (qd / "quote.json").exists() and (qd / "measurements.md").exists() and (qd / "REQ-0001-r1-3d-viewer.html").exists()
    ob = T.outbox(t)
    assert ob["to"] == ["ana@example.org"] and len(ob["attachments"]) == 2
    assert T.send_quote(t, dry_run=True)["sent"] is False
    T.record_sent(t, "<m1@x>", "th1"); T.save_ticket(t)
    assert t["status"] == "quoted" and t["quotes"][0]["sent"]
    # the mailbox: a reply with notes, a brand-new request, my own mail on the thread, junk
    sync = tmp_path / "sync"; sync.mkdir()
    (sync / "mail.json").write_text(json.dumps([
        {"id": "<r1@x>", "thread_id": "th1", "from": "ana@example.org", "subject": "Re: [REQ-0001] Quote r1: A corner bracket",
         "date": "2026-09-11T08:00:00", "text": "Could you make the arms 50 mm?\n\nOn Wed wrote:\n> Hi Ana"},
        {"id": "<me@x>", "thread_id": "th1", "from": "me@shop.org", "subject": "Re: [REQ-0001] Quote r1", "date": "2026-09-11T08:30:00", "text": "sure"},
        {"id": "<new@x>", "from": "bo@example.org", "from_name": "Bo Chen", "subject": "[print request] Phone stand",
         "date": "2026-09-11T09:00:00", "text": "What is it for: recipes\nSizes it must fit (mm): 160 x 75 x 9"},
        {"id": "<junk@x>", "from": "spam@x.org", "subject": "hello", "date": "2026-09-11T09:30:00", "text": "hi"},
    ]), encoding="utf-8")
    s = T.ingest(sync, mine={"me@shop.org"})
    assert [r["verdict"] for r in s["replies"]] == ["changes"] and s["new"][0]["ticket"] == "REQ-0002" and len(s["skipped"]) == 1
    t1 = T.load_ticket("REQ-0001"); t2 = T.load_ticket("REQ-0002")
    assert t1["status"] == "changes" and [m["kind"] for m in t1["messages"]] == ["request", "quote", "reply", "mail"]
    assert t1["messages"][2]["text"] == "Could you make the arms 50 mm?"
    assert t2["requester"] == {"name": "Bo Chen", "email": "bo@example.org"} and "Your e-mail" not in t2["request"]["text"]
    assert s["new"][0]["missing"] == []     # name/e-mail came from the headers, title from the subject
    # ingest is idempotent, and a CONFIRM approves
    assert T.ingest(sync, mine={"me@shop.org"})["replies"] == []
    (sync / "mail.json").write_text(json.dumps([{"id": "<r2@x>", "from": "ana@example.org", "subject": "Re: [REQ-0001] Quote r2",
                                                 "date": "2026-09-12T08:00:00", "text": "Confirm, please print it"}]), encoding="utf-8")
    T.ingest(sync, mine={"me@shop.org"})
    assert T.load_ticket("REQ-0001")["status"] == "approved"
    # a request typed on the board page
    (sync / "requests.json").write_text(json.dumps([{"id": "d1", "fields": {"name": "Cy", "email": "cy@x.org", "title": "Hook"}, "created": "2026-09-12T10:00:00"}]), encoding="utf-8")
    s = T.ingest(sync, mine={"me@shop.org"})
    assert s["requests_filed"][0]["ticket"] == "REQ-0003" and "What is it for" in s["requests_filed"][0]["missing"]
    actions = json.loads((sync / "actions.json").read_text(encoding="utf-8"))
    assert actions[0]["doc_id"] == "d1" and actions[0]["data"]["ticket"] == "REQ-0003"
    assert T.ingest(sync, mine={"me@shop.org"})["requests_filed"] == []
    board = T.format_board({"repo": "x", "inbox": "me@shop.org", "tickets": [T.ticket_summary(x) for x in T.list_tickets()], "pages": {}})
    assert "APPROVED (1)" in board and "REQ-0003" in board and "MISSING" in board
    assert "QUOTES" in T.format_ticket(T.load_ticket("REQ-0001"))


def test_pages_render(tmp_path):
    d = T.page_data()
    req = T.write_html(d, "request", tmp_path / "requests.html").read_text(encoding="utf-8")
    board = T.write_html(d, "board", tmp_path / "tickets.html").read_text(encoding="utf-8")
    for page in (req, board):
        assert "__DATA__" not in page and "__TITLE__" not in page
    assert "<title>Request a print</title>" in req and '"tickets": []' in req and '"pricing"' not in req    # nothing internal on the public page
    assert "Tickets</title>" in board


# ---------------------------------------------------------------- Jira mode (scripts/jira_api.py), against a fake Jira

class FakeJira:
    """Just enough of Jira Cloud + JSM to run pull / attach / transition through the real client code."""
    def __init__(self):
        self.calls = []
        self.comments = [{"id": "7", "body": "Could the arms be 50 mm?", "public": True, "created": {"iso8601": "2026-09-11T08:00:00+0000"},
                          "author": {"accountId": "cust1", "displayName": "Ana Ruiz", "emailAddress": "ana@example.org"}},
                         {"id": "8", "body": "internal note", "public": False, "created": {"iso8601": "2026-09-11T08:30:00+0000"},
                          "author": {"accountId": "me1", "displayName": "Me"}}]
        self.status = "Waiting for support"

    def __call__(self, method, url, headers, body):
        import json as J
        from urllib.parse import urlparse, parse_qs
        u = urlparse(url); path = u.path; q = parse_qs(u.query)
        self.calls.append((method, path, body))
        assert headers["Authorization"].startswith("Basic ")
        def ok(x): return 200, J.dumps(x).encode()
        if path == "/rest/api/3/myself":
            return ok({"accountId": "me1", "displayName": "Me", "emailAddress": "me@shop.org"})
        if path == "/rest/api/3/search/jql":
            assert "project" in q["jql"][0]
            return ok({"issues": [{"key": "PRINT-12", "fields": {"summary": "Corner bracket", "status": {"name": self.status}, "created": "2026-09-11T07:00:00.000+0000",
                                                                  "updated": "2026-09-11T08:30:00.000+0000", "reporter": {"accountId": "cust1", "displayName": "Ana Ruiz"},
                                                                  "description": {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "shelf to stud"}]}]}}}]})
        if path == "/rest/servicedeskapi/request/PRINT-12":
            return ok({"issueKey": "PRINT-12", "serviceDeskId": "3", "requestTypeId": "21", "createdDate": {"iso8601": "2026-09-11T07:00:00+0000"},
                       "reporter": {"accountId": "cust1", "displayName": "Ana Ruiz", "emailAddress": "ana@example.org"},
                       "currentStatus": {"status": self.status},
                       "requestFieldValues": [{"fieldId": "summary", "label": "Summary", "value": "Corner bracket"},
                                              {"fieldId": "description", "label": "Description", "value": "Holding a 12 mm plywood shelf to a stud."},
                                              {"fieldId": "customfield_1", "label": "Sizes it must fit (mm)", "value": "arms ~40, M4"},
                                              {"fieldId": "customfield_2", "label": "How many", "value": "4"},
                                              {"fieldId": "customfield_3", "label": "Colour", "value": "black PETG"}]})
        if path == "/rest/servicedeskapi/request/PRINT-12/comment" and method == "GET":
            return ok({"values": self.comments, "isLastPage": True})
        if path == "/rest/servicedeskapi/servicedesk/3/attachTemporaryFile":
            assert headers["X-Atlassian-Token"] == "no-check" and b'filename="measurements.md"' in body
            return 201, J.dumps({"temporaryAttachments": [{"temporaryAttachmentId": "tmp1", "fileName": "x"}, {"temporaryAttachmentId": "tmp2", "fileName": "y"}]}).encode()
        if path == "/rest/servicedeskapi/request/PRINT-12/attachment":
            b = J.loads(body); assert b["public"] and b["temporaryAttachmentIds"] == ["tmp1", "tmp2"] and "CONFIRM" in b["additionalComment"]["body"]
            return 201, J.dumps({"comment": {"id": "9"}}).encode()
        if path == "/rest/api/3/issue/PRINT-12/transitions" and method == "GET":
            return ok({"transitions": [{"id": "11", "name": "Start progress", "to": {"name": "In progress"}},
                                       {"id": "21", "name": "Respond to customer", "to": {"name": "Waiting for customer"}},
                                       {"id": "31", "name": "Resolve this issue", "to": {"name": "Resolved"}}]})
        if path == "/rest/api/3/issue/PRINT-12/transitions" and method == "POST":
            b = J.loads(body); self.status = {"11": "In progress", "21": "Waiting for customer", "31": "Resolved"}[b["transition"]["id"]]
            return 204, b""
        if path == "/rest/servicedeskapi/servicedesk":
            return ok({"values": [{"id": "3", "projectKey": "PRINT", "projectName": "Print shop"}]})
        raise AssertionError(f"unexpected {method} {path}")


def test_jira_pull_maps_portal_fields_and_comments():
    from scripts import jira_api
    fake = FakeJira()
    client = jira_api.JiraClient("https://x.atlassian.net", "me@shop.org", "tok", transport=fake)
    cfg = {"project": "PRINT", "service_desk_id": "3", "field_labels": {"Colour": "material"}}
    reqs = jira_api.pull(client, cfg, T.jira_field_map(cfg))
    assert len(reqs) == 1 and reqs[0]["key"] == "PRINT-12" and reqs[0]["url"] == "https://x.atlassian.net/browse/PRINT-12"
    f = reqs[0]["fields"]
    assert f["title"] == "Corner bracket" and f["purpose"].startswith("Holding") and f["dimensions"] == "arms ~40, M4" and f["quantity"] == "4" and f["material"] == "black PETG"
    assert reqs[0]["reporter"]["email"] == "ana@example.org" and reqs[0]["status"] == "Waiting for support" and reqs[0]["jsm"]
    assert [c["who"] for c in reqs[0]["comments"]] == ["requester", "me"] and reqs[0]["comments"][0]["created"] == "2026-09-11T08:00:00"
    assert jira_api.adf_text({"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "a"}, {"type": "hardBreak"}, {"type": "text", "text": "b"}]}]}) == "a\nb\n"
    assert jira_api.adf_from_text("one\ntwo\n\nthree")["content"][1]["content"][0]["text"] == "three"


def test_jira_ingest_send_and_set(tmp_path, monkeypatch):
    from scripts import jira_api
    monkeypatch.setattr(T, "TICKETS_DIR", tmp_path / "tickets")
    monkeypatch.setattr(T, "list_projects", lambda: ["demo"])
    monkeypatch.setattr(T, "MODELS_DIR", tmp_path / "models")
    (tmp_path / "models" / "demo" / "exports" / "renders").mkdir(parents=True)
    (tmp_path / "models" / "demo" / "exports" / "build_report.json").write_text(json.dumps(REPORT), encoding="utf-8")
    (tmp_path / "models" / "demo" / "exports" / "view.html").write_text("<p>viewer</p>", encoding="utf-8")
    fake = FakeJira()
    client = jira_api.JiraClient("https://x.atlassian.net", "me@shop.org", "tok", transport=fake)
    cfg = {"project": "PRINT", "service_desk_id": "3", "field_labels": {"Colour": "material"}, "transitions": jira_api.DEFAULT_TRANSITIONS}
    monkeypatch.setattr(T, "load_jira_cfg", lambda: cfg)
    monkeypatch.setattr(T, "jira_client", lambda c=None: (client, cfg))
    # pull -> ingest: a new ticket keyed by the Jira key; the customer's comment before any quote is a note, not a verdict
    sync = tmp_path / "sync"; sync.mkdir()
    (sync / "jira.json").write_text(json.dumps(T.jira_fetch()), encoding="utf-8")
    s = T.ingest(sync, mine={"me@shop.org"})
    assert s["new"][0]["ticket"] == "PRINT-12" and s["new"][0]["missing"] == []
    t = T.load_ticket("PRINT-12")
    assert t["id"] == "PRINT-12" and t["jira"]["key"] == "PRINT-12" and t["status"] == "new" and t["requester"]["email"] == "ana@example.org"
    assert [m["kind"] for m in t["messages"]] == ["request", "reply", "internal"] and s["replies"][0]["verdict"] == "note"
    assert T.next_id() == "REQ-0001"                      # Jira keys do not disturb the mail-mode counter
    # quote + send: a public comment with the package attached, then the 'quoted' transition
    T.make_quote(t, "demo"); T.save_ticket(t)
    r = T.jira_send_quote(t)
    assert r["comment_id"] == "9" and r["attached"] == ["PRINT-12-r1-3d-viewer.html", "measurements.md"] and r["transition"] == "Jira: Respond to customer -> Waiting for customer"
    T.record_sent(t, f"jira-comment-{r['comment_id']}"); T.save_ticket(t)
    assert t["status"] == "quoted" and t["jira"]["status"] == "Waiting for customer" and fake.status == "Waiting for customer"
    # the customer confirms in Jira -> approved; the internal comment is not fed back twice
    fake.comments.append({"id": "10", "body": "Confirm — go ahead", "public": True, "created": {"iso8601": "2026-09-12T09:00:00+0000"},
                          "author": {"accountId": "cust1", "displayName": "Ana Ruiz", "emailAddress": "ana@example.org"}})
    (sync / "jira.json").write_text(json.dumps(T.jira_fetch()), encoding="utf-8")
    s = T.ingest(sync, mine={"me@shop.org"})
    t = T.load_ticket("PRINT-12")
    assert s["replies"] == [{"ticket": "PRINT-12", "verdict": "approved", "text": "Confirm — go ahead", "from": "ana@example.org"}]
    assert t["status"] == "approved" and len([m for m in t["messages"] if m["kind"] == "internal"]) == 1
    assert T.ingest(sync, mine={"me@shop.org"})["replies"] == []
    # set done -> the configured transition
    assert T.jira_transition(t, "done", client=client, cfg=cfg) == "Jira: Resolve this issue -> Resolved"
    assert T.jira_transition(t, "approved", client=client, cfg=cfg).startswith("Jira: no transition")
