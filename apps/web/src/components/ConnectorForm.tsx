import { useForm, type FieldValues, type Resolver } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Select } from "./ui/select";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "./ui/form";
import { ConnectorSchema } from "../lib/connectors";

interface Props {
  schema: ConnectorSchema;
  initial?: Record<string, any>;
  submitting?: boolean;
  onSubmit: (values: Record<string, any>) => void;
  onCancel?: () => void;
}

export function ConnectorForm({ schema, initial, submitting, onSubmit, onCancel }: Props) {
  const defaults = Object.fromEntries(
    schema.fields.map((f) => [f.key, initial?.[f.key] ?? f.default ?? ""])
  );

  const form = useForm<FieldValues>({
    resolver: zodResolver(schema.zod as any) as Resolver<FieldValues>,
    defaultValues: defaults,
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        {schema.fields.map((spec) => (
          <FormField
            key={spec.key}
            control={form.control}
            name={spec.key}
            render={({ field }) => (
              <FormItem>
                <FormLabel>
                  {spec.label}
                  {spec.required && <span className="text-destructive ml-1">*</span>}
                </FormLabel>
                <FormControl>
                  {spec.type === "select" ? (
                    <Select {...field}>
                      {(spec.options || []).map((opt) => (
                        <option key={opt} value={opt}>{opt}</option>
                      ))}
                    </Select>
                  ) : (
                    <Input
                      type={spec.type === "number" ? "number" : spec.type === "password" ? "password" : spec.type === "url" ? "url" : "text"}
                      placeholder={spec.placeholder}
                      {...field}
                    />
                  )}
                </FormControl>
                {spec.helper && <p className="text-xs text-mute mt-1">{spec.helper}</p>}
                <FormMessage />
              </FormItem>
            )}
          />
        ))}
        <div className="flex justify-end gap-2 pt-2">
          {onCancel && (
            <Button type="button" variant="outline" onClick={onCancel}>Cancel</Button>
          )}
          <Button type="submit" disabled={submitting}>
            {submitting ? "Saving…" : "Save & connect"}
          </Button>
        </div>
      </form>
    </Form>
  );
}
