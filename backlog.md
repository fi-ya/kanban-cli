# CoSpace Initial Product Backlog

## Story 1: View Available Desks

As an employee, I want to see which desks are available for a selected date so that I can choose where to work before making a booking.

### Acceptance Criteria

- Given I select a valid future or current date, when I view desk availability, then I see only desks that are not already booked for that date.
- Given all desks are booked for the selected date, when I view availability, then I see a clear message that no desks are available.
- Given I enter an invalid date, when I request availability, then the system explains the date format required and does not show misleading results.

## Story 2: Book a Desk

As an employee, I want to book one available desk for a selected date so that I have a confirmed workspace when I come into the office.

### Acceptance Criteria

- Given a desk is available on the selected date, when I book it, then the booking is created and linked to my name or user ID.
- Given a desk is already booked on the selected date, when I try to book it, then the system rejects the request and tells me the desk is unavailable.
- Given my booking is successful, when the confirmation is shown, then it includes the desk, date, and booking reference.

## Story 3: Cancel a Booking

As an employee, I want to cancel one of my future desk bookings so that the desk becomes available if my plans change.

### Acceptance Criteria

- Given I have a future booking, when I cancel it, then the booking status changes to cancelled.
- Given a booking has been cancelled, when other employees view availability for that date, then the desk appears as available.
- Given I try to cancel a booking that does not exist or is not mine, when I submit the cancellation, then the system rejects it with a clear message.

## Story 4: View My Bookings

As an employee, I want to view my upcoming desk bookings so that I can plan my office days.

### Acceptance Criteria

- Given I have upcoming bookings, when I view my bookings, then they are shown in date order.
- Given I have no upcoming bookings, when I view my bookings, then I see a clear empty-state message.
- Given cancelled or past bookings exist, when I view upcoming bookings, then they are not mixed into the active upcoming list.

## Story 5: Prevent Double Booking

As an office coordinator, I want the system to prevent two employees from booking the same desk on the same date so that desk availability remains accurate.

### Acceptance Criteria

- Given two booking requests target the same desk and date, when the first request succeeds, then the second request is rejected.
- Given a rejected duplicate booking attempt occurs, when the user sees the result, then the message explains that the desk is already booked.
- Given a booking is cancelled, when another employee books the same desk for that date, then the new booking is allowed.