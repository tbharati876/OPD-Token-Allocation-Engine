# OPD Token Allocation Engine

A robust, priority based appointment management system designed for hospital Outpatient Departments (OPD). This engine handles elastic capacity, multiple booking sources, and real-time emergency insertions using a sophisticated queuing algorithm.

---

## Features
- **Dynamic Prioritization**: Automatically sorts patients based on medical urgency and booking type.
- **Elastic Capacity**: Enforces hard limits for standard bookings while allowing "Emergency" overrides.
- **Multi-Doctor Support**: Manages independent queues for multiple doctors and time slots.
- **Live Dashboard**: Real time queue visualization with time synchronization.

---

## The Algorithm: Priority Min-Heap
The core logic utilizes a **Min-Heap** data structure ($O(\log n)$ insertion). This ensures the doctor always sees the highest-priority patient next without manual sorting. Each patient is stored as a tuple:
` (Priority_Rank, Arrival_Time, Patient_Data) `

1. **Primary Sort (Priority_Rank)**: Lower numerical values (0) take precedence over higher values (4).
2. **Secondary Sort (Arrival_Time)**: If priority ranks are equal, the system reverts to **FCFS (First-Come, First-Served)** based on the exact time of entry.

### Priority Mapping Table
| Category | Rank | Policy |
| :--- | :---: | :--- |
| **EMERGENCY** | 0 | Bypasses slot limits; immediate insertion at top of the queue. |
| **PAID** | 1 | Priority over standard and follow-up bookings. |
| **FOLLOW_UP** | 2 | Standard priority for returning patients. |
| **ONLINE** | 3 | Standard priority for web/app bookings. |
| **WALK_IN** | 4 | Baseline priority for on-site registrations. |

---

## Tech Stack
- **Backend**: Python 3.x, Flask
- **Data Structures**: `heapq` (Priority Queue implementation)
- **Time Management**: `pytz` (IST Time synchronization)
- **Frontend**: (Async/Fetch), Bootstrap 5, CSS3
- **Tunneling**: `pyngrok` for external API accessibility

---

## API Reference

### 1. Book a Token
**Endpoint:** `POST /api/book`  
**Payload:**
```json
{
  "doctor": "Dr. Smith",
  "slot": "09:00-10:00",
  "name": "Rajesh Kumar",
  "category": "PAID"
}
2. Get Live Queue
Endpoint: GET /api/queue?doctor=Dr. Smith&slot=09:00-10:00

Returns: A sorted list of patients based on the priority algorithm.

## Installation & Setup
Clone the repository

Install dependencies

Bash
pip install flask pyngrok pytz
Configure Ngrok Update the NGROK_TOKEN in the script with your token from ngrok.com.

Run the Application

Bash
python app.py

Edge Case Handling
Slot Saturation: Standard bookings are capped at 5 patients per slot. If a user attempts to book a 6th patient, the system returns an error unless the category is "EMERGENCY".

Timezone Integrity: By using pytz, the system avoids "server time" drift, ensuring "Arrival Time" is always consistent with the hospital's local time (IST).

Concurrency: The heap based sorting ensures that even if two patients are added within seconds, their position in the queue is mathematically determined and stable.

Future Roadmap
Persistence: Migration from in-memory storage to SQLite or Redis to prevent data loss on restarts.

Cancellation Flow: Implementing a DELETE method to remove patients and instantly re-calculate the queue.

Doctor's "Next" Button: A specialized UI for doctors to "Pop" the top patient from the heap once the consultation is finished.

SMS Integration: Automated alerts via Twilio when a patient's position is within the next 2 spots.
