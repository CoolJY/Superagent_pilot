import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import type { ComponentProps } from "react";
import type { CopilotChatView } from "@copilotkit/react-core/v2";

vi.mock("@/lib/deployment", () => ({ AIR_GAP_MODE: true }));
vi.mock("@copilotkit/react-core/v2", () => ({
  CopilotChatView: (props: ComponentProps<typeof CopilotChatView>) => <>
    <input aria-label="Message" value={props.inputValue} onChange={(event) => props.onInputChange?.(event.target.value)} />
    <button onClick={() => props.onSubmitMessage?.(props.inputValue ?? "")}>Send</button>
  </>,
}));
import { ProviderKeysProvider, useProviderKeys } from "./provider-keys";
import { KeyGatedChatView } from "./key-gated-chat-view";
const submit = vi.fn();
function Harness() {
  const { headers, keysOpen } = useProviderKeys();
  return <><KeyGatedChatView onSubmitMessage={submit} /><span>{JSON.stringify({ headers, keysOpen })}</span></>;
}
afterEach(() => { cleanup(); vi.clearAllMocks(); });
it("sends the first message without a provider-key dialog or credential headers", () => {
  render(<ProviderKeysProvider><Harness /></ProviderKeysProvider>);
  fireEvent.change(screen.getByLabelText("Message"), { target: { value: "안녕" } });
  fireEvent.click(screen.getByText("Send"));
  expect(submit).toHaveBeenCalledExactlyOnceWith("안녕");
  expect(screen.getByText('{"keysOpen":false}')).toBeInTheDocument();
});
