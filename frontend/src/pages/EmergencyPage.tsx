import { ResourcePage } from "../components/ResourcePage";
import { EmergencyForm } from "../forms/EmergencyForm";
import { LookupData } from "../types";

export function EmergencyPage({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  return (
    <ResourcePage
      title="File urgences"
      path="/emergency/queue"
      form={<EmergencyForm lookups={lookups} onCreated={onCreated} />}
    />
  );
}
