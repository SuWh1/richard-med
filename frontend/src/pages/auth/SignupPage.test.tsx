import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { signup } from "@/lib/auth-client";
import { SignupPage } from "./SignupPage";

const navigate = vi.fn();
vi.mock("react-router-dom", async (orig) => ({
  ...(await orig<typeof import("react-router-dom")>()),
  useNavigate: () => navigate,
}));
vi.mock("@/lib/auth-client", () => ({ signup: vi.fn() }));

describe("SignupPage (raw email/password, no OTP)", () => {
  beforeEach(() => vi.clearAllMocks());

  it("should register and go straight to the cabinet (no OTP step)", async () => {
    vi.mocked(signup).mockResolvedValue({
      user: { id: 1, email: "a@b.com", name: null, role: "user" },
    });
    render(
      <MemoryRouter>
        <SignupPage />
      </MemoryRouter>,
    );

    await userEvent.type(screen.getByLabelText("Email"), "a@b.com");
    await userEvent.type(screen.getByLabelText("Пароль"), "secret123");
    await userEvent.click(screen.getByRole("button", { name: "Зарегистрироваться" }));

    await waitFor(() => expect(signup).toHaveBeenCalled());
    expect(navigate).toHaveBeenCalledWith("/cabinet");
  });
});
