from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build


@dataclass
class ListingText:
    title: str = ""
    short_description: str = ""
    full_description: str = ""


class GooglePlayConsoleTool:
    def __init__(self, service_account_file: str, package_name: str):
        self.package_name = package_name
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=["https://www.googleapis.com/auth/androidpublisher"],
        )
        self.service = build("androidpublisher", "v3", credentials=credentials, cache_discovery=False)

    def _insert_edit(self) -> str:
        edit = self.service.edits().insert(body={}, packageName=self.package_name).execute()
        return edit["id"]

    def _commit_edit(self, edit_id: str) -> None:
        self.service.edits().commit(packageName=self.package_name, editId=edit_id).execute()

    def get_listing_text(self, locale: str) -> ListingText:
        edit_id = self._insert_edit()
        listing = self.service.edits().listings().get(
            packageName=self.package_name,
            editId=edit_id,
            language=locale,
        ).execute()
        return ListingText(
            title=listing.get("title", ""),
            short_description=listing.get("shortDescription", ""),
            full_description=listing.get("fullDescription", ""),
        )

    def list_filled_locales(self) -> Dict[str, ListingText]:
        edit_id = self._insert_edit()
        response = self.service.edits().listings().list(
            packageName=self.package_name,
            editId=edit_id,
        ).execute()
        result: Dict[str, ListingText] = {}
        for item in response.get("listings", []):
            locale = item.get("language")
            if not locale:
                continue
            result[locale] = ListingText(
                title=item.get("title", ""),
                short_description=item.get("shortDescription", ""),
                full_description=item.get("fullDescription", ""),
            )
        return result

    def export_listings_to_json(self, output_file: str) -> int:
        data = self.list_filled_locales()
        payload = {
            "packageName": self.package_name,
            "listings": {locale: asdict(text) for locale, text in data.items()},
        }
        Path(output_file).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return len(data)

    def import_listings_from_json(self, input_file: str) -> Dict[str, str]:
        payload = json.loads(Path(input_file).read_text(encoding="utf-8"))
        listings = payload.get("listings", {})
        if not isinstance(listings, dict):
            raise ValueError("Некорректный JSON: поле 'listings' должно быть объектом")

        edit_id = self._insert_edit()
        result: Dict[str, str] = {}
        for locale, values in listings.items():
            body = {
                "language": locale,
                "title": values.get("title", ""),
                "shortDescription": values.get("short_description", values.get("shortDescription", "")),
                "fullDescription": values.get("full_description", values.get("fullDescription", "")),
            }
            self.service.edits().listings().patch(
                packageName=self.package_name,
                editId=edit_id,
                language=locale,
                body=body,
            ).execute()
            result[locale] = "updated"
        self._commit_edit(edit_id)
        return result

    def copy_listing_text(self, source_locale: str, target_locales: Iterable[str]) -> Dict[str, str]:
        src = self.get_listing_text(source_locale)
        edit_id = self._insert_edit()
        results: Dict[str, str] = {}
        for locale in target_locales:
            body = {
                "language": locale,
                "title": src.title,
                "shortDescription": src.short_description,
                "fullDescription": src.full_description,
            }
            self.service.edits().listings().patch(
                packageName=self.package_name,
                editId=edit_id,
                language=locale,
                body=body,
            ).execute()
            results[locale] = "ok"
        self._commit_edit(edit_id)
        return results

    def upload_images_from_master_folder(
        self,
        image_type: str,
        master_folder: str,
        target_locales: Optional[Iterable[str]] = None,
    ) -> Dict[str, int]:
        edit_id = self._insert_edit()
        root = Path(master_folder)
        locales = [p for p in root.iterdir() if p.is_dir()]
        if target_locales:
            allowed = set(target_locales)
            locales = [p for p in locales if p.name in allowed]

        result: Dict[str, int] = {}
        for locale_dir in locales:
            locale = locale_dir.name
            files = sorted(
                [
                    p
                    for p in locale_dir.iterdir()
                    if p.is_file() and p.suffix.lower().lstrip(".") in {"jpg", "jpeg", "png", "webp"}
                ],
                key=lambda p: p.name,
            )
            uploaded = 0
            for img in files:
                self.service.edits().images().upload(
                    packageName=self.package_name,
                    editId=edit_id,
                    language=locale,
                    imageType=image_type,
                    media_body=img.as_posix(),
                ).execute()
                uploaded += 1
            result[locale] = uploaded

        self._commit_edit(edit_id)
        return result

    def delete_all_images(self, image_type: str, locales: Iterable[str]) -> Dict[str, str]:
        edit_id = self._insert_edit()
        result: Dict[str, str] = {}
        for locale in locales:
            self.service.edits().images().deleteall(
                packageName=self.package_name,
                editId=edit_id,
                language=locale,
                imageType=image_type,
            ).execute()
            result[locale] = "deleted"
        self._commit_edit(edit_id)
        return result
