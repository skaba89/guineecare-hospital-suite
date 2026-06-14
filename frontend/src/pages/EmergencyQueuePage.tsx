import { ResourcePage } from "../components/ResourcePage";
import { EmergencyForm } from "../forms/EmergencyForm";
import { LookupData } from "../types";

export function EmergencyQueuePage({ lookups, onCreated }: { lookups: LookupData; onCreated: () => void }) {
  return (
    <ResourcePage
      title="File des passages"
      path="/emergency/queue"
      form={<EmergencyForm lookups={lookups} onCreated={onCreated} />}
    />
  );
}
