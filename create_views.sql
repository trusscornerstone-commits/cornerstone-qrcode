-- ============================================================
-- 1) Função: converte "46-02-08" → pés decimais (NUMERIC)
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
-- 2) View detalhada: vw_production_clean
-- ============================================================

DROP VIEW IF EXISTS public.vw_production_clean;
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
    p.production_date,
    p.create_date,
    p.update_date,
    p.span AS span_raw,

    public.parse_span_feet(p.span) AS span_feet,

    CASE 
        WHEN public.parse_span_feet(p.span) IS NOT NULL 
        THEN public.parse_span_feet(p.span) * 0.3048 
        ELSE NULL 
    END AS span_meters,

    public.parse_span_feet(p.span) AS span_planned_feet,

    CASE 
        WHEN p.produced THEN public.parse_span_feet(p.span)
        ELSE 0 
    END AS span_produced_feet,

    CASE 
        WHEN p.produced THEN 1.0 ELSE 0.0 
    END AS percent_done

FROM public.qr_codetrusses p;


-- ============================================================
-- 3) View agregada por truss_id + dimensões de tempo e local
-- ============================================================

DROP VIEW IF EXISTS public.vw_production_truss_summary CASCADE;
CREATE VIEW public.vw_production_truss_summary AS
SELECT
    p.truss_id,
    MIN(p.project) AS project,
    MIN(p.floor) AS floor,
    MIN(p.table_number) AS table_number,

    -- Datas para filtros
    DATE_TRUNC('day', MIN(p.production_date))::DATE AS production_day,
    DATE_TRUNC('month', MIN(p.production_date))::DATE AS production_month,

    COUNT(*) AS total_planned,
    SUM(CASE WHEN p.produced THEN 1 ELSE 0 END) AS total_produced,

    CASE 
        WHEN COUNT(*) = 0 THEN 0
        ELSE SUM(CASE WHEN p.produced THEN 1 ELSE 0 END)::NUMERIC / COUNT(*)
    END AS percent_done,

    SUM(COALESCE(public.parse_span_feet(p.span), 0)) AS span_planned_feet,
    SUM(CASE WHEN p.produced THEN COALESCE(public.parse_span_feet(p.span), 0) ELSE 0 END) AS span_produced_feet,

    MAX(p.update_date) AS last_update_date,

    SUM(
        CASE 
            WHEN p.produced AND p.production_date >= (now() - interval '1 hour') 
            THEN 1 ELSE 0 
        END
    ) AS produced_last_hour

FROM public.qr_codetrusses p
GROUP BY 
    p.truss_id,
    p.floor,
    p.table_number,
    DATE_TRUNC('day', p.production_date),
    DATE_TRUNC('month', p.production_date)
ORDER BY 
    p.truss_id;


-- ============================================================
-- 4) Materialized view opcional
-- ============================================================

DROP MATERIALIZED VIEW IF EXISTS public.mvw_production_truss_summary;
CREATE MATERIALIZED VIEW public.mvw_production_truss_summary AS
SELECT * FROM public.vw_production_truss_summary
WITH NO DATA;


-- ============================================================
-- 5) View geral com dimensões de tempo e local
-- ============================================================

DROP VIEW IF EXISTS public.vw_production_overview;
CREATE VIEW public.vw_production_overview AS
SELECT
    production_month,
    production_day,
    floor,
    table_number,
    SUM(total_planned) AS total_planned,
    SUM(total_produced) AS total_produced,
    CASE 
        WHEN SUM(total_planned) = 0 THEN 0
        ELSE SUM(total_produced)::NUMERIC / SUM(total_planned)
    END AS percent_done,
    SUM(span_planned_feet) AS span_planned_feet,
    SUM(span_produced_feet) AS span_produced_feet,
    MAX(last_update_date) AS last_update_date,
    SUM(produced_last_hour) AS produced_last_hour
FROM 
    public.vw_production_truss_summary
GROUP BY 
    production_month, production_day, floor, table_number
ORDER BY 
    production_month DESC, production_day DESC;
