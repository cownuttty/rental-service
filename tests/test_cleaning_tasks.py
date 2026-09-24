from tests.base import ApiTestCase


class CleaningTaskCrudTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.apartment = self.make_apartment()
        self.cleaner = self.make_cleaner()

    def _create_task(self, **overrides):
        payload = {"apartment_id": self.apartment["id"], "scheduled_date": "2026-10-05"}
        payload.update(overrides)
        return self._create("/cleaning-tasks", payload)

    def test_create_task_defaults(self):
        task = self._create_task()
        self.assertEqual(task["status"], "planned")
        self.assertEqual(task["cost"], 0)
        self.assertIsNone(task["cleaner_id"])

    def test_create_task_with_cleaner_and_cost(self):
        task = self._create_task(cleaner_id=self.cleaner["id"], cost=1200)
        self.assertEqual(task["cleaner_id"], self.cleaner["id"])
        self.assertEqual(task["cost"], 1200)

    def test_create_task_missing_fields(self):
        response = self.client.post("/cleaning-tasks", json={"apartment_id": self.apartment["id"]})
        self.assertEqual(response.status_code, 400)

    def test_create_task_unknown_apartment(self):
        response = self.client.post(
            "/cleaning-tasks", json={"apartment_id": 999, "scheduled_date": "2026-10-05"}
        )
        self.assertEqual(response.status_code, 400)

    def test_create_task_invalid_date_and_cost(self):
        for field, value in (("scheduled_date", "05.10.2026"), ("cost", -5), ("status", "x")):
            with self.subTest(field=field):
                payload = {"apartment_id": self.apartment["id"], "scheduled_date": "2026-10-05"}
                payload[field] = value
                self.assertEqual(self.client.post("/cleaning-tasks", json=payload).status_code, 400)

    def test_inactive_cleaner_cannot_be_assigned(self):
        self.client.put(f"/cleaners/{self.cleaner['id']}", json={"is_active": False})
        response = self.client.post(
            "/cleaning-tasks",
            json={"apartment_id": self.apartment["id"], "scheduled_date": "2026-10-05",
                  "cleaner_id": self.cleaner["id"]},
        )
        self.assertEqual(response.status_code, 400)

    def test_list_and_filter_tasks(self):
        self._create_task(cleaner_id=self.cleaner["id"])
        self._create_task(scheduled_date="2026-10-06")
        self.assertEqual(len(self.client.get("/cleaning-tasks").get_json()), 2)
        by_cleaner = self.client.get(f"/cleaning-tasks?cleaner_id={self.cleaner['id']}")
        self.assertEqual(len(by_cleaner.get_json()), 1)
        by_date = self.client.get("/cleaning-tasks?date=2026-10-06")
        self.assertEqual(len(by_date.get_json()), 1)

    def test_get_task(self):
        task = self._create_task()
        response = self.client.get(f"/cleaning-tasks/{task['id']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["scheduled_date"], "2026-10-05")

    def test_get_task_not_found(self):
        self.assertEqual(self.client.get("/cleaning-tasks/999").status_code, 404)

    def test_update_task_assign_cleaner_and_finish(self):
        task = self._create_task()
        response = self.client.put(
            f"/cleaning-tasks/{task['id']}",
            json={"cleaner_id": self.cleaner["id"], "status": "done", "cost": 1500},
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["status"], "done")
        self.assertEqual(body["cleaner_id"], self.cleaner["id"])

    def test_delete_task(self):
        task = self._create_task()
        self.assertEqual(self.client.delete(f"/cleaning-tasks/{task['id']}").status_code, 204)
        self.assertEqual(self.client.get(f"/cleaning-tasks/{task['id']}").status_code, 404)

    def test_deleting_cleaner_keeps_task_without_cleaner(self):
        task = self._create_task(cleaner_id=self.cleaner["id"])
        self.client.delete(f"/cleaners/{self.cleaner['id']}")
        result = self.client.get(f"/cleaning-tasks/{task['id']}").get_json()
        self.assertIsNone(result["cleaner_id"])

    def test_deleting_apartment_removes_its_tasks(self):
        task = self._create_task()
        self.client.delete(f"/apartments/{self.apartment['id']}")
        self.assertEqual(self.client.get(f"/cleaning-tasks/{task['id']}").status_code, 404)


class AutoCleaningTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.apartment = self.make_apartment()
        self.guest = self.make_client()
        self.booking = self.make_booking(self.apartment["id"], self.guest["id"])  # выезд 05.10

    def test_completing_booking_creates_cleaning_task(self):
        self.client.put(f"/bookings/{self.booking['id']}", json={"status": "completed"})
        tasks = self.client.get("/cleaning-tasks").get_json()
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["booking_id"], self.booking["id"])
        self.assertEqual(tasks[0]["scheduled_date"], "2026-10-05")  # день выезда
        self.assertEqual(tasks[0]["status"], "planned")

    def test_other_statuses_do_not_create_task(self):
        self.client.put(f"/bookings/{self.booking['id']}", json={"status": "confirmed"})
        self.assertEqual(self.client.get("/cleaning-tasks").get_json(), [])

    def test_task_is_not_duplicated(self):
        url = f"/bookings/{self.booking['id']}"
        self.client.put(url, json={"status": "completed"})
        self.client.put(url, json={"status": "completed"})
        self.assertEqual(len(self.client.get("/cleaning-tasks").get_json()), 1)

    def test_deleting_booking_keeps_task(self):
        self.client.put(f"/bookings/{self.booking['id']}", json={"status": "completed"})
        self.client.delete(f"/bookings/{self.booking['id']}")
        tasks = self.client.get("/cleaning-tasks").get_json()
        self.assertEqual(len(tasks), 1)
        self.assertIsNone(tasks[0]["booking_id"])
