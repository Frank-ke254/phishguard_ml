from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

import joblib
import pandas as pd


BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
ARTIFACTS_DIR = ROOT_DIR / "model" / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "phishing_model.pkl"
FEATURES_PATH = ARTIFACTS_DIR / "feature_columns.pkl"

SENSITIVE_KEYWORDS = {
    "login",
    "verify",
    "secure",
    "account",
    "update",
    "password",
    "bank",
}


class Predictor:
    def __init__(self) -> None:
        self.model = joblib.load(MODEL_PATH)
        self.feature_columns: list[str] = joblib.load(FEATURES_PATH)

    def predict_url(self, url: str) -> dict:
        feature_row = self._extract_features(url)
        frame = pd.DataFrame([feature_row], columns=self.feature_columns)
        label = int(self.model.predict(frame)[0])

        if hasattr(self.model, "predict_proba"):
            confidence = float(self.model.predict_proba(frame)[0][label])
        else:
            confidence = 0.5

        return {
            "url": url,
            "label": label,
            "prediction": "phishing" if label == 1 else "safe",
            "confidence": round(confidence, 4),
            "risk_flags": self._risk_flags(feature_row),
            "recommended_action": self._recommended_action(label, confidence),
        }

    def predict_batch(self, urls: list[str]) -> dict:
        results = [self.predict_url(url) for url in urls]
        phishing_count = sum(item["label"] == 1 for item in results)
        safe_count = len(results) - phishing_count
        high_risk_count = sum(
            item["label"] == 1 and float(item["confidence"]) >= 0.8 for item in results
        )
        return {
            "total": len(results),
            "phishing_count": phishing_count,
            "safe_count": safe_count,
            "high_risk_count": high_risk_count,
            "results": results,
        }

    def _extract_features(self, url: str) -> dict:
        parsed = urlparse(url)
        host = parsed.netloc or ""
        path = parsed.path or ""
        query = parsed.query or ""

        subdomain_level = max(host.count(".") - 1, 0) if host else 0
        domain_core = host.split(".")[0] if host else ""

        row = {name: 0 for name in self.feature_columns}

        derived = {
            "NumDots": url.count("."),
            "SubdomainLevel": subdomain_level,
            "PathLevel": path.count("/"),
            "UrlLength": len(url),
            "NumDash": url.count("-"),
            "NumDashInHostname": host.count("-"),
            "AtSymbol": int("@" in url),
            "TildeSymbol": int("~" in url),
            "NumUnderscore": url.count("_"),
            "NumPercent": url.count("%"),
            "NumQueryComponents": len([p for p in query.split("&") if p]) if query else 0,
            "NumAmpersand": query.count("&"),
            "NumHash": url.count("#"),
            "NumNumericChars": sum(c.isdigit() for c in url),
            "NoHttps": int(parsed.scheme.lower() != "https"),
            "RandomString": int(bool(re.search(r"[A-Za-z0-9]{12,}", url))),
            "IpAddress": int(bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host))),
            "DomainInSubdomains": int(domain_core.lower() in host.lower().split(".")[0:-2])
            if host.count(".") >= 2
            else 0,
            "DomainInPaths": int(domain_core.lower() in path.lower()) if domain_core else 0,
            "HttpsInHostname": int("https" in host.lower()),
            "HostnameLength": len(host),
            "PathLength": len(path),
            "QueryLength": len(query),
            "DoubleSlashInPath": int("//" in path),
            "NumSensitiveWords": sum(word in url.lower() for word in SENSITIVE_KEYWORDS),
            "EmbeddedBrandName": 0,
            "PctExtHyperlinks": 0.0,
            "PctExtResourceUrls": 0.0,
            "ExtFavicon": 0,
            "InsecureForms": 0,
            "RelativeFormAction": 0,
            "ExtFormAction": 0,
            "AbnormalFormAction": 0,
            "PctNullSelfRedirectHyperlinks": 0.0,
            "FrequentDomainNameMismatch": 0,
            "FakeLinkInStatusBar": 0,
            "RightClickDisabled": 0,
            "PopUpWindow": 0,
            "SubmitInfoToEmail": 0,
            "IframeOrFrame": 0,
            "MissingTitle": 0,
            "ImagesOnlyInForm": 0,
            "SubdomainLevelRT": 0,
            "UrlLengthRT": 0,
            "PctExtResourceUrlsRT": 0,
            "AbnormalExtFormActionR": 0,
            "ExtMetaScriptLinkRT": 0,
            "PctExtNullSelfRedirectHyperlinksRT": 0,
        }

        for key, value in derived.items():
            if key in row:
                row[key] = value
        return row

    def _risk_flags(self, feature_row: dict) -> list[str]:
        flags: list[str] = []
        if feature_row.get("NoHttps", 0) == 1:
            flags.append("URL does not use HTTPS")
        if feature_row.get("IpAddress", 0) == 1:
            flags.append("Domain appears to be an IP address")
        if feature_row.get("AtSymbol", 0) == 1:
            flags.append("Contains @ symbol")
        if feature_row.get("DoubleSlashInPath", 0) == 1:
            flags.append("Contains double slash in path")
        if feature_row.get("NumSensitiveWords", 0) >= 2:
            flags.append("Contains multiple sensitive keywords")
        if feature_row.get("UrlLength", 0) >= 90:
            flags.append("Unusually long URL")
        return flags

    def _recommended_action(self, label: int, confidence: float) -> str:
        if label == 1 and confidence >= 0.8:
            return "Block and escalate for security review."
        if label == 1:
            return "Treat as suspicious and verify destination independently."
        if confidence < 0.6:
            return "Low-confidence safe result. Validate before sharing."
        return "Likely safe. Continue with standard caution."
