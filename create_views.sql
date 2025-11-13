-- ============================================================
-- LIMPEZA GERAL (remove antigas para evitar conflito)
-- ============================================================

DROP VIEW IF EXISTS public.vw_production_summary_by_table CASCADE;
DROP VIEW IF EXISTS public.vw_production_overview_full CASCADE;
DROP VIEW IF EXISTS public.vw_production_clean CASCADE;

-- ============================================================
-- 1) Função utilitária: converte "46-02-08" → pés decimais
-- ============================================================

CREATE OR REPLACE FUNCTION public.parse_span_feet(span_text TEXT)
RETURNS NUMERIC LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE
    parts TEXT[];
    feet NUMERIC := 0;
    inches NUMERIC := 0;
    sixteenths NUMERIC := 0;
    total_in_inches NUMERIC := 0;
    total_feet NUMERIC := NULL;
BEGIN
    IF span_text IS NULL OR trim(span_text) = '' THEN
        RETURN NULL;
    END IF;

    span_text := trim(span_text);
    parts := string_to_array(span_text, '-');

    IF array_length(parts,1) >= 1 THEN
        BEGIN feet := parts[1]::NUMERIC; EXCEPTION WHEN others THEN feet := 0; END;
    END IF;

    IF array_length(parts,1) >= 2 THEN
        BEGIN inches := parts[2]::NUMERIC; EXCEPTION WHEN others THEN inches := 0; END;
    END IF;

    IF array_length(parts,1) >= 3 THEN
        BEGIN sixteenths := parts[3]::NUMERIC; EXCEPTION WHEN others THEN sixteenths := 0; END;
    END IF;

    total_in_inches := (feet * 12) + inches + (sixteenths / 16.0);
    total_feet := total_in_inches / 12.0;

    RETURN total_feet;
END;
$$;

-- ============================================================
-- 2) View detalhada base (com datas formatadas e fuso de NY)
-- ============================================================

CREATE VIEW public.vw_production_clean AS
SELECT
    p.id,
    p.truss_id,
    p.serial_number,
    p.project,
    p.floor,
    p.table_number,
    p.producer_name,
    p.unit_number,
    p.quantity,
    p.produced,

    -- Conversão de datas com fuso horário
    (p.production_date AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York') AS production_date_ny,
    TO_CHAR((p.production_date AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York'), 'YYYY-MM-DD HH24:MI:SS') AS production_date_text,

    (p.create_date AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York') AS create_date_ny,
    TO_CHAR((p.create_date AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York'), 'YYYY-MM-DD HH24:MI:SS') AS create_date_text,

    (p.update_date AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York') AS update_date_ny,
    TO_CHAR((p.update_date AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York'), 'YYYY-MM-DD HH24:MI:SS') AS update_date_text,

    DATE_TRUNC('day', p.production_date AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York')::DATE AS production_day,
    DATE_TRUNC('month', p.production_date AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York')::DATE AS production_month,

    p.span AS span_raw,
    public.parse_span_feet(p.span) AS span_feet,
    public.parse_span_feet(p.span) * 0.3048 AS span_meters,

    CASE WHEN p.produced THEN public.parse_span_feet(p.span) ELSE 0 END AS span_produced_feet,
    CASE WHEN p.produced THEN 1 ELSE 0 END AS produced_flag

FROM public.qr_codetrusses p;

-- ============================================================
-- 3) View principal: vw_production_overview_full
-- ============================================================

CREATE VIEW public.vw_production_overview_full AS
WITH base AS (
    SELECT
        project,
        floor,
        table_number,
        production_day,
        production_month,
        produced,
        span_feet,
        span_produced_feet,
        update_date_ny,
        production_date_ny,
        produced_flag,
        -- totais globais fixos (chumbados)
        COUNT(*) OVER () AS total_planned_global,
        SUM(span_feet) OVER () AS total_span_global
    FROM public.vw_production_clean
),
days AS (
    SELECT DISTINCT production_day FROM base WHERE production_day IS NOT NULL
),
aggregated AS (
    SELECT
        d.production_day,
        b.production_month,
        b.project,
        b.floor,
        b.table_number,
        MAX(b.update_date_ny) AS last_update_date,
        MAX(b.production_date_ny) AS last_production_date,

        MAX(b.total_planned_global) AS total_planned,
        MAX(b.total_span_global) AS span_planned_feet,

        SUM(b.produced_flag) FILTER (WHERE b.production_day <= d.production_day) AS total_produced,

        CASE 
            WHEN MAX(b.total_planned_global) = 0 THEN 0
            ELSE SUM(b.produced_flag) FILTER (WHERE b.production_day <= d.production_day)::NUMERIC
                 / MAX(b.total_planned_global)
        END AS percent_done,

        (MAX(b.total_span_global) *
            CASE 
                WHEN MAX(b.total_planned_global) = 0 THEN 0
                ELSE SUM(b.produced_flag) FILTER (WHERE b.production_day <= d.production_day)::NUMERIC
                     / MAX(b.total_planned_global)
            END
        ) AS span_produced_feet,

        SUM(CASE WHEN b.production_date_ny >= (NOW() AT TIME ZONE 'America/New_York' - INTERVAL '1 hour') THEN 1 ELSE 0 END) AS produced_last_hour

    FROM base b
    CROSS JOIN days d
    WHERE b.production_day <= d.production_day
    GROUP BY d.production_day, b.floor, b.table_number, b.project, b.production_month
)
SELECT
    production_month,
    production_day,
    project,
    floor,
    table_number,
    total_planned,
    total_produced,
    percent_done,
    span_planned_feet,
    ROUND(span_produced_feet::numeric, 2)::DOUBLE PRECISION AS span_produced_feet,
    last_update_date,
    last_production_date,
    produced_last_hour
FROM aggregated
ORDER BY production_day, floor, table_number;

-- ============================================================
-- 4) View adicional: resumo por mesa (vw_production_summary_by_table)
-- ============================================================

CREATE VIEW public.vw_production_summary_by_table AS
SELECT
    DATE_TRUNC('month', p.production_date AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York')::DATE AS production_month,
    DATE_TRUNC('day', p.production_date AT TIME ZONE 'UTC' AT TIME ZONE 'America/New_York')::DATE AS production_day,
    p.table_number,
    COUNT(*) FILTER (WHERE p.produced = TRUE) AS qty_truss,
    SUM(public.parse_span_feet(p.span)) FILTER (WHERE p.produced = TRUE) AS total_lf,
    STRING_AGG(DISTINCT p.producer_name, ', ') AS resp
FROM public.qr_codetrusses p
GROUP BY production_month, production_day, p.table_number
ORDER BY production_day, p.table_number;
