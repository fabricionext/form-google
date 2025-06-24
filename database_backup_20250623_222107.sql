--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: drizzle; Type: SCHEMA; Schema: -; Owner: form_user
--

CREATE SCHEMA drizzle;


ALTER SCHEMA drizzle OWNER TO form_user;

--
-- Name: testimonial_source; Type: TYPE; Schema: public; Owner: form_user
--

CREATE TYPE public.testimonial_source AS ENUM (
    'manual',
    'google'
);


ALTER TYPE public.testimonial_source OWNER TO form_user;

--
-- Name: tipopessoaenum; Type: TYPE; Schema: public; Owner: form_user
--

CREATE TYPE public.tipopessoaenum AS ENUM (
    'FISICA',
    'JURIDICA'
);


ALTER TYPE public.tipopessoaenum OWNER TO form_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: __drizzle_migrations; Type: TABLE; Schema: drizzle; Owner: form_user
--

CREATE TABLE drizzle.__drizzle_migrations (
    id integer NOT NULL,
    hash text NOT NULL,
    created_at bigint
);


ALTER TABLE drizzle.__drizzle_migrations OWNER TO form_user;

--
-- Name: __drizzle_migrations_id_seq; Type: SEQUENCE; Schema: drizzle; Owner: form_user
--

CREATE SEQUENCE drizzle.__drizzle_migrations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE drizzle.__drizzle_migrations_id_seq OWNER TO form_user;

--
-- Name: __drizzle_migrations_id_seq; Type: SEQUENCE OWNED BY; Schema: drizzle; Owner: form_user
--

ALTER SEQUENCE drizzle.__drizzle_migrations_id_seq OWNED BY drizzle.__drizzle_migrations.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: form_user
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO form_user;

--
-- Name: autoridades_transito; Type: TABLE; Schema: public; Owner: form_user
--

CREATE TABLE public.autoridades_transito (
    id integer NOT NULL,
    nome character varying(255) NOT NULL,
    cnpj character varying(18),
    logradouro character varying(255),
    numero character varying(50),
    complemento character varying(100),
    cidade character varying(100),
    estado character varying(2),
    cep character varying(9)
);


ALTER TABLE public.autoridades_transito OWNER TO form_user;

--
-- Name: autoridades_transito_id_seq; Type: SEQUENCE; Schema: public; Owner: form_user
--

CREATE SEQUENCE public.autoridades_transito_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.autoridades_transito_id_seq OWNER TO form_user;

--
-- Name: autoridades_transito_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: form_user
--

ALTER SEQUENCE public.autoridades_transito_id_seq OWNED BY public.autoridades_transito.id;


--
-- Name: clientes_peticionador; Type: TABLE; Schema: public; Owner: form_user
--

CREATE TABLE public.clientes_peticionador (
    id integer NOT NULL,
    tipo_pessoa public.tipopessoaenum NOT NULL,
    email character varying(128) NOT NULL,
    telefone_celular character varying(32),
    nome_completo character varying(128),
    cpf character varying(14),
    razao_social character varying(128),
    cnpj character varying(18),
    representante_nome character varying(128)
);


ALTER TABLE public.clientes_peticionador OWNER TO form_user;

--
-- Name: clientes_peticionador_id_seq; Type: SEQUENCE; Schema: public; Owner: form_user
--

CREATE SEQUENCE public.clientes_peticionador_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.clientes_peticionador_id_seq OWNER TO form_user;

--
-- Name: clientes_peticionador_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: form_user
--

ALTER SEQUENCE public.clientes_peticionador_id_seq OWNED BY public.clientes_peticionador.id;


--
-- Name: document_templates; Type: TABLE; Schema: public; Owner: form_user
--

CREATE TABLE public.document_templates (
    id integer NOT NULL,
    tipo_pessoa character varying(10) NOT NULL,
    nome character varying(150) NOT NULL,
    template_id character varying(64) NOT NULL
);


ALTER TABLE public.document_templates OWNER TO form_user;

--
-- Name: document_templates_id_seq; Type: SEQUENCE; Schema: public; Owner: form_user
--

CREATE SEQUENCE public.document_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.document_templates_id_seq OWNER TO form_user;

--
-- Name: document_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: form_user
--

ALTER SEQUENCE public.document_templates_id_seq OWNED BY public.document_templates.id;


--
-- Name: formulario_gerado; Type: TABLE; Schema: public; Owner: form_user
--

CREATE TABLE public.formulario_gerado (
    id integer NOT NULL,
    cliente_id integer NOT NULL,
    modelo_id integer NOT NULL,
    dados_preenchidos json NOT NULL,
    status character varying(50) NOT NULL,
    data_geracao timestamp without time zone NOT NULL,
    data_envio timestamp without time zone,
    observacoes text
);


ALTER TABLE public.formulario_gerado OWNER TO form_user;

--
-- Name: formulario_gerado_id_seq; Type: SEQUENCE; Schema: public; Owner: form_user
--

CREATE SEQUENCE public.formulario_gerado_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.formulario_gerado_id_seq OWNER TO form_user;

--
-- Name: formulario_gerado_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: form_user
--

ALTER SEQUENCE public.formulario_gerado_id_seq OWNED BY public.formulario_gerado.id;


--
-- Name: formularios_gerados; Type: TABLE; Schema: public; Owner: form_user
--

CREATE TABLE public.formularios_gerados (
    id integer NOT NULL,
    modelo_id integer NOT NULL,
    nome character varying(150) NOT NULL,
    slug character varying(150) NOT NULL,
    criado_em timestamp without time zone
);


ALTER TABLE public.formularios_gerados OWNER TO form_user;

--
-- Name: formularios_gerados_id_seq; Type: SEQUENCE; Schema: public; Owner: form_user
--

CREATE SEQUENCE public.formularios_gerados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.formularios_gerados_id_seq OWNER TO form_user;

--
-- Name: formularios_gerados_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: form_user
--

ALTER SEQUENCE public.formularios_gerados_id_seq OWNED BY public.formularios_gerados.id;


--
-- Name: peticao_modelos; Type: TABLE; Schema: public; Owner: form_user
--

CREATE TABLE public.peticao_modelos (
    id integer NOT NULL,
    nome character varying(150) NOT NULL,
    doc_template_id character varying(64) NOT NULL,
    pasta_destino_id character varying(64) NOT NULL,
    descricao text,
    ativo boolean,
    criado_em timestamp without time zone
);


ALTER TABLE public.peticao_modelos OWNER TO form_user;

--
-- Name: peticao_modelos_id_seq; Type: SEQUENCE; Schema: public; Owner: form_user
--

CREATE SEQUENCE public.peticao_modelos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.peticao_modelos_id_seq OWNER TO form_user;

--
-- Name: peticao_modelos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: form_user
--

ALTER SEQUENCE public.peticao_modelos_id_seq OWNED BY public.peticao_modelos.id;


--
-- Name: peticao_placeholders; Type: TABLE; Schema: public; Owner: form_user
--

CREATE TABLE public.peticao_placeholders (
    id integer NOT NULL,
    modelo_id integer NOT NULL,
    chave character varying(64) NOT NULL,
    tipo_campo character varying(20) NOT NULL,
    label_form character varying(120),
    opcoes_json text,
    ordem integer,
    obrigatorio boolean DEFAULT true NOT NULL
);


ALTER TABLE public.peticao_placeholders OWNER TO form_user;

--
-- Name: peticao_placeholders_id_seq; Type: SEQUENCE; Schema: public; Owner: form_user
--

CREATE SEQUENCE public.peticao_placeholders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.peticao_placeholders_id_seq OWNER TO form_user;

--
-- Name: peticao_placeholders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: form_user
--

ALTER SEQUENCE public.peticao_placeholders_id_seq OWNED BY public.peticao_placeholders.id;


--
-- Name: peticoes_geradas; Type: TABLE; Schema: public; Owner: form_user
--

CREATE TABLE public.peticoes_geradas (
    id integer NOT NULL,
    cliente_id integer,
    modelo character varying(120) NOT NULL,
    google_id character varying(64) NOT NULL,
    link character varying(255),
    criado_em timestamp without time zone
);


ALTER TABLE public.peticoes_geradas OWNER TO form_user;

--
-- Name: peticoes_geradas_id_seq; Type: SEQUENCE; Schema: public; Owner: form_user
--

CREATE SEQUENCE public.peticoes_geradas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.peticoes_geradas_id_seq OWNER TO form_user;

--
-- Name: peticoes_geradas_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: form_user
--

ALTER SEQUENCE public.peticoes_geradas_id_seq OWNED BY public.peticoes_geradas.id;


--
-- Name: respostas_form; Type: TABLE; Schema: public; Owner: form_user
--

CREATE TABLE public.respostas_form (
    id integer NOT NULL,
    timestamp_processamento timestamp without time zone,
    submission_id character varying(64) NOT NULL,
    tipo_pessoa character varying(16),
    primeiro_nome character varying(64),
    sobrenome character varying(64),
    cpf character varying(32),
    data_nascimento character varying(16),
    rg character varying(32),
    estado_emissor_rg character varying(32),
    nacionalidade character varying(32),
    estado_civil character varying(32),
    profissao character varying(64),
    cnh character varying(32),
    razao_social character varying(128),
    cnpj character varying(32),
    nome_representante_legal character varying(128),
    cpf_representante_legal character varying(32),
    cargo_representante_legal character varying(64),
    cep character varying(16),
    endereco character varying(128),
    logradouro character varying(128),
    numero character varying(16),
    complemento character varying(64),
    bairro character varying(64),
    cidade character varying(64),
    uf_endereco character varying(32),
    telefone_celular character varying(32),
    outro_telefone character varying(32),
    email character varying(128),
    nome_cliente_pasta character varying(128),
    ids_arquivos_anexados character varying(256),
    link_pasta_cliente character varying(256),
    status_processamento character varying(64),
    observacoes_processamento text
);


ALTER TABLE public.respostas_form OWNER TO form_user;

--
-- Name: respostas_form_id_seq; Type: SEQUENCE; Schema: public; Owner: form_user
--

CREATE SEQUENCE public.respostas_form_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.respostas_form_id_seq OWNER TO form_user;

--
-- Name: respostas_form_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: form_user
--

ALTER SEQUENCE public.respostas_form_id_seq OWNED BY public.respostas_form.id;


--
-- Name: users_peticionador; Type: TABLE; Schema: public; Owner: form_user
--

CREATE TABLE public.users_peticionador (
    id integer NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(256),
    name character varying(100),
    is_active boolean
);


ALTER TABLE public.users_peticionador OWNER TO form_user;

--
-- Name: users_peticionador_id_seq; Type: SEQUENCE; Schema: public; Owner: form_user
--

CREATE SEQUENCE public.users_peticionador_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_peticionador_id_seq OWNER TO form_user;

--
-- Name: users_peticionador_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: form_user
--

ALTER SEQUENCE public.users_peticionador_id_seq OWNED BY public.users_peticionador.id;


--
-- Name: __drizzle_migrations id; Type: DEFAULT; Schema: drizzle; Owner: form_user
--

ALTER TABLE ONLY drizzle.__drizzle_migrations ALTER COLUMN id SET DEFAULT nextval('drizzle.__drizzle_migrations_id_seq'::regclass);


--
-- Name: autoridades_transito id; Type: DEFAULT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.autoridades_transito ALTER COLUMN id SET DEFAULT nextval('public.autoridades_transito_id_seq'::regclass);


--
-- Name: clientes_peticionador id; Type: DEFAULT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.clientes_peticionador ALTER COLUMN id SET DEFAULT nextval('public.clientes_peticionador_id_seq'::regclass);


--
-- Name: document_templates id; Type: DEFAULT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.document_templates ALTER COLUMN id SET DEFAULT nextval('public.document_templates_id_seq'::regclass);


--
-- Name: formulario_gerado id; Type: DEFAULT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.formulario_gerado ALTER COLUMN id SET DEFAULT nextval('public.formulario_gerado_id_seq'::regclass);


--
-- Name: formularios_gerados id; Type: DEFAULT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.formularios_gerados ALTER COLUMN id SET DEFAULT nextval('public.formularios_gerados_id_seq'::regclass);


--
-- Name: peticao_modelos id; Type: DEFAULT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.peticao_modelos ALTER COLUMN id SET DEFAULT nextval('public.peticao_modelos_id_seq'::regclass);


--
-- Name: peticao_placeholders id; Type: DEFAULT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.peticao_placeholders ALTER COLUMN id SET DEFAULT nextval('public.peticao_placeholders_id_seq'::regclass);


--
-- Name: peticoes_geradas id; Type: DEFAULT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.peticoes_geradas ALTER COLUMN id SET DEFAULT nextval('public.peticoes_geradas_id_seq'::regclass);


--
-- Name: respostas_form id; Type: DEFAULT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.respostas_form ALTER COLUMN id SET DEFAULT nextval('public.respostas_form_id_seq'::regclass);


--
-- Name: users_peticionador id; Type: DEFAULT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.users_peticionador ALTER COLUMN id SET DEFAULT nextval('public.users_peticionador_id_seq'::regclass);


--
-- Data for Name: __drizzle_migrations; Type: TABLE DATA; Schema: drizzle; Owner: form_user
--

COPY drizzle.__drizzle_migrations (id, hash, created_at) FROM stdin;
1	e5d8f88f2cc36b32ee0af29c0f650de014f0518935293ddb9f41f3d43c3b6850	1750021166794
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: form_user
--

COPY public.alembic_version (version_num) FROM stdin;
ca54ea9654ed
\.


--
-- Data for Name: autoridades_transito; Type: TABLE DATA; Schema: public; Owner: form_user
--

COPY public.autoridades_transito (id, nome, cnpj, logradouro, numero, complemento, cidade, estado, cep) FROM stdin;
\.


--
-- Data for Name: clientes_peticionador; Type: TABLE DATA; Schema: public; Owner: form_user
--

COPY public.clientes_peticionador (id, tipo_pessoa, email, telefone_celular, nome_completo, cpf, razao_social, cnpj, representante_nome) FROM stdin;
1	FISICA	teste.auto@example.com	11999999999	Teste Automacao	11122233344	\N	\N	\N
2	FISICA	joao.silva@exemplo.com	(11) 98765-4321	João Silva	123.456.789-00	\N	\N	\N
\.


--
-- Data for Name: document_templates; Type: TABLE DATA; Schema: public; Owner: form_user
--

COPY public.document_templates (id, tipo_pessoa, nome, template_id) FROM stdin;
\.


--
-- Data for Name: formulario_gerado; Type: TABLE DATA; Schema: public; Owner: form_user
--

COPY public.formulario_gerado (id, cliente_id, modelo_id, dados_preenchidos, status, data_geracao, data_envio, observacoes) FROM stdin;
\.


--
-- Data for Name: formularios_gerados; Type: TABLE DATA; Schema: public; Owner: form_user
--

COPY public.formularios_gerados (id, modelo_id, nome, slug, criado_em) FROM stdin;
10	1	Suspensão do Direito de Dirigir - Junho 2025	suspens-o-do-direito-de-dirigir---junho-2025-6c61399d	2025-06-23 16:19:32.957618
\.


--
-- Data for Name: peticao_modelos; Type: TABLE DATA; Schema: public; Owner: form_user
--

COPY public.peticao_modelos (id, nome, doc_template_id, pasta_destino_id, descricao, ativo, criado_em) FROM stdin;
1	Suspensão do Direito de Dirigir	1hTaBuBs20oY0xgexdm-d8RBpiRORcPQOmrRGQe9rx_Y	1LvPsvml7bkN2TQjyAqnNAYAy7qRebrDf	Esse é um modelo de suspensão do direito de dirigir	t	2025-06-17 23:59:26.082514
\.


--
-- Data for Name: peticao_placeholders; Type: TABLE DATA; Schema: public; Owner: form_user
--

COPY public.peticao_placeholders (id, modelo_id, chave, tipo_campo, label_form, opcoes_json, ordem, obrigatorio) FROM stdin;
1	1	endereco_cep	string	Endereço Cep	\N	11	t
2	1	sobrenome	string	Sobrenome	\N	2	t
3	1	endereco_bairro	string	Endereço Bairro	\N	10	t
4	1	profissao	string	Profissão	\N	5	t
5	1	endereco_logradouro	string	Endereço Logradouro	\N	7	t
7	1	endereco_cidade	string	Endereço Cidade	\N	12	t
8	1	endereco_estado	string	Endereço Estado	\N	13	t
9	1	rg	string	Rg	\N	14	t
11	1	nacionalidade	string	Nacionalidade	\N	3	t
12	1	endereco_numero	string	Endereço Numero	\N	8	t
13	1	cnh	string	Cnh	\N	16	t
14	1	endereco_complemento	string	Endereço Complemento	\N	9	t
15	1	cpf	string	Cpf	\N	6	t
17	1	primeiro_nome	string	Primeiro Nome	\N	1	t
18	1	estado_emissor_do_rg	string	Estado Emissor Do Rg	\N	15	t
19	1	estado_civil	string	Estado Civil	\N	4	t
20	1	estado_Civil	string	Estado Civil	\N	7	t
21	1	profissão	string	Profissão	\N	9	t
22	1	endereço_Logradouro	string	Endereço Logradouro	\N	11	t
23	1	Endereço_Numero	string	Endereço Numero	\N	12	t
24	1	endereço_complemento	string	Endereço Complemento	\N	13	t
25	1	endereço_bairro	string	Endereço Bairro	\N	14	t
26	1	endereço_cidade	string	Endereço Cidade	\N	15	t
27	1	endereço_estado	string	Endereço Estado	\N	16	t
28	1	endereço_cep	string	Endereço Cep	\N	17	t
16	1	processo_numero	string	Processo Numero	\N	17	t
10	1	total_pontos	string	Total Pontos	\N	18	t
6	1	data_atual	string	Data Atual	\N	19	t
\.


--
-- Data for Name: peticoes_geradas; Type: TABLE DATA; Schema: public; Owner: form_user
--

COPY public.peticoes_geradas (id, cliente_id, modelo, google_id, link, criado_em) FROM stdin;
2	\N	Suspensão do Direito de Dirigir	1HpB94nvSqVMp8tPy9g6dnFAmDDY8Zkb_iXmyXDDg59Q	https://docs.google.com/document/d/1HpB94nvSqVMp8tPy9g6dnFAmDDY8Zkb_iXmyXDDg59Q/edit?usp=drivesdk	2025-06-23 16:23:04.111995
3	\N	Suspensão do Direito de Dirigir	1HpB94nvSqVMp8tPy9g6dnFAmDDY8Zkb_iXmyXDDg59Q	https://docs.google.com/document/d/1HpB94nvSqVMp8tPy9g6dnFAmDDY8Zkb_iXmyXDDg59Q/edit?usp=drivesdk	2025-06-23 16:31:17.855677
4	\N	Suspensão do Direito de Dirigir	1HpB94nvSqVMp8tPy9g6dnFAmDDY8Zkb_iXmyXDDg59Q	https://docs.google.com/document/d/1HpB94nvSqVMp8tPy9g6dnFAmDDY8Zkb_iXmyXDDg59Q/edit?usp=drivesdk	2025-06-23 16:43:16.396339
5	\N	Suspensão do Direito de Dirigir	1HpB94nvSqVMp8tPy9g6dnFAmDDY8Zkb_iXmyXDDg59Q	https://docs.google.com/document/d/1HpB94nvSqVMp8tPy9g6dnFAmDDY8Zkb_iXmyXDDg59Q/edit?usp=drivesdk	2025-06-23 16:55:28.221844
6	\N	Suspensão do Direito de Dirigir	1HpB94nvSqVMp8tPy9g6dnFAmDDY8Zkb_iXmyXDDg59Q	https://docs.google.com/document/d/1HpB94nvSqVMp8tPy9g6dnFAmDDY8Zkb_iXmyXDDg59Q/edit?usp=drivesdk	2025-06-23 16:57:44.188703
\.


--
-- Data for Name: respostas_form; Type: TABLE DATA; Schema: public; Owner: form_user
--

COPY public.respostas_form (id, timestamp_processamento, submission_id, tipo_pessoa, primeiro_nome, sobrenome, cpf, data_nascimento, rg, estado_emissor_rg, nacionalidade, estado_civil, profissao, cnh, razao_social, cnpj, nome_representante_legal, cpf_representante_legal, cargo_representante_legal, cep, endereco, logradouro, numero, complemento, bairro, cidade, uf_endereco, telefone_celular, outro_telefone, email, nome_cliente_pasta, ids_arquivos_anexados, link_pasta_cliente, status_processamento, observacoes_processamento) FROM stdin;
1	2025-06-18 11:28:00.732237	164c2ec4-7a2c-4d8e-a5d5-8ec0b351a62b	PF	Teste	Cascade	171.871.360-01	01/01/2000	99.888.777-6	\N	Brasileira	Solteira	IA	\N	\N	\N	\N	\N	\N	94043-000	\N	\N	42	\N	Silicio	Vale	CA	(11) 99999-8888	\N	teste.cascade.1718713600@windsurf.dev	\N	\N	https://drive.google.com/drive/folders/1FRcyWZB18VChbi8Z05vndn45O5HT92bE	Pendente	Registro criado via API de geração de documentos
2	2025-06-18 11:35:52.730666	0abcc6b1-c076-48f6-9076-ffee2b9198b6	PF	Teste	Cascade	171.871.360-01	01/01/2000	99.888.777-6	\N	Brasileira	Solteira	IA	\N	\N	\N	\N	\N	\N	94043-000	\N	\N	42	\N	Silicio	Vale	CA	(11) 99999-8888	\N	teste.cascade.1718713600@windsurf.dev	\N	\N	https://drive.google.com/drive/folders/1FRcyWZB18VChbi8Z05vndn45O5HT92bE	Pendente	Registro criado via API de geração de documentos
3	2025-06-18 11:52:38.143008	1793cdcd-7974-4903-92f2-595b00c3a805	PF	Teste	Cascade	171.871.360-01	01/01/2000	99.888.777-6	\N	Brasileira	Solteira	IA	\N	\N	\N	\N	\N	\N	94043-000	\N	\N	42	\N	Silicio	Vale	CA	(11) 99999-8888	\N	teste.cascade.1718713600@windsurf.dev	\N	\N	https://drive.google.com/drive/folders/1FRcyWZB18VChbi8Z05vndn45O5HT92bE	Pendente	Registro criado via API de geração de documentos
4	2025-06-18 12:09:06.132885	686a5609-a63b-406c-9327-9745f2fcf4e0	PF	Estevao API Key	Almeida Completo	123.456.789-00	01/01/1980	\N	\N	Brasileiro	Casado	Desenvolvedor	\N	\N	\N	\N	\N	\N	01000-000	\N	Rua dos Bobos	0	\N	Centro	São Paulo	SP	(11) 99999-8888	\N	estevao.almeida.apikey@windsurf.dev	\N	\N	https://drive.google.com/drive/folders/1ueO_BGAU0wBzJj5gttwKSCNHBoslOXe3	Pendente	Registro criado via API de geração de documentos
5	2025-06-18 19:56:16.139878	5ccbe533-f7f1-4b5a-8f9e-e0c3d522783d	PF	Maria	SantosAPI	00011122233	15/05/1990	7654321	RJ	Brasileira	Solteira	Advogada	\N	\N	\N	\N	\N	\N	20000000	\N	Avenida Teste API	456	\N	Bairro Novo API	Rio de Janeiro	RJ	21988887777	\N	maria.santos.testeapi01@example.com	\N	\N	https://drive.google.com/drive/folders/18B4hYApIQSsViye6TAkkwdjTzCJoQusw	Pendente	Registro criado via API de geração de documentos
6	2025-06-18 20:54:06.736687	test_submission_1750290846.693039	pf	Cliente	Teste Peticionador	11122233344	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	peticionador.teste@example.com	\N	\N	\N	Completo	\N
7	2025-06-21 10:54:18.000014	c4ad993e-c25b-4295-b145-07b81e42cb69	PF	Teste	Almeida	000.000.000-00	1900-01-01	00.000.000-0	PE	Brasileiro(a)	Divorciado(a)	Teste	\N	\N	\N	\N	\N	\N	86010-001	\N	Rua Professor João Cândido	00	de 1061/1062 ao fim	Centro	Londrina	PR	(99) 99999-9999		teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/14uvdEj8boiISoa0IsQKACm4ZxufWOCJx	Pendente	Registro criado via API de geração de documentos
8	2025-06-21 10:55:25.602026	c90b5500-93ba-43b7-bf35-c67dab11ebee	PF	Teste	Almeida	000.000.000-00	1900-01-01	000000	PA	Brasileiro(a)	Divorciado(a)	Teste	\N	\N	\N	\N	\N	\N	86010-001	\N	Rua Professor João Cândido	00	de 1061/1062 ao fim	Centro	Londrina	PR	(99) 99999-9999		teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/14uvdEj8boiISoa0IsQKACm4ZxufWOCJx	Pendente	Registro criado via API de geração de documentos
9	2025-06-21 10:56:36.853794	da54ecff-f009-4b1a-b645-a9ef3f103f8c	PF	Teste	Almeida	000.000.000-00	1900-01-01	000000	PA	Brasileiro(a)	Divorciado(a)	Teste	\N	\N	\N	\N	\N	\N	86010-001	\N	Rua Professor João Cândido	00	de 1061/1062 ao fim	Centro	Londrina	PR	(99) 99999-9999		teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/14uvdEj8boiISoa0IsQKACm4ZxufWOCJx	Pendente	Registro criado via API de geração de documentos
10	2025-06-22 12:27:49.513591	cbf19052-05c8-4369-a2f1-43b8a4122789	PF	Teste	Bot	12345678901	1990-05-01	123456 SSP/UF	\N	brasileira	solteiro(a)	engenheiro	\N	\N	\N	\N	\N	\N	01001-000	\N	\N	123	Apto 45	Centro	São Paulo	SP	(11) 91234-5678	\N	teste.bot@example.com	\N	\N	https://drive.google.com/drive/folders/1TVCtlHBNLQp7Hp8uHW7nuz6csjIFH8QX	Pendente	Registro criado via API de geração de documentos
11	2025-06-22 12:47:36.257223	6885fbf3-ace5-4cbc-97b2-849251cd8181	PF	Teste	Bot	12345678901	1990-05-01	123456 SSP/UF	\N	brasileira	solteiro(a)	engenheiro	\N	\N	\N	\N	\N	\N	01001-000	\N	\N	123	Apto 45	Centro	São Paulo	SP	(11) 91234-5678	\N	teste.bot@example.com	\N	\N	https://drive.google.com/drive/folders/1TVCtlHBNLQp7Hp8uHW7nuz6csjIFH8QX	Pendente	Registro criado via API de geração de documentos
12	2025-06-22 12:54:24.363835	3cb63dc4-d122-4776-8d83-73da5e742782	PF	Teste	Bot	12345678901	1990-05-01	123456 SSP/UF	\N	brasileira	solteiro(a)	engenheiro	\N	\N	\N	\N	\N	\N	01001-000	\N	\N	123	Apto 45	Centro	São Paulo	SP	(11) 91234-5678	\N	teste.bot@example.com	\N	\N	https://drive.google.com/drive/folders/1TVCtlHBNLQp7Hp8uHW7nuz6csjIFH8QX	Pendente	Registro criado via API de geração de documentos
13	2025-06-22 13:12:05.505253	task-295e7914-7305-494d-9125-90cddabe7ecb	pf	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Falha_orquestracao	'tuple' object has no attribute 'get'
14	2025-06-22 13:13:28.246116	task-60091fbf-2d2f-420d-9c6c-802c7de7ac23	pf	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	Falha_orquestracao	too many values to unpack (expected 2)
19	2025-06-22 13:32:34.284074	task-d8471b25-501d-4afc-8293-976fc741aa6e	pf	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	https://drive.google.com/drive/folders/1sj2B1eDXigpvvev8Bzckoh8d14xHdYvY	Concluido	{"links": []}
17	2025-06-22 13:22:14.242544	task-4e340b80-9274-4699-bcc4-dd7bd99434ee	pf	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	https://drive.google.com/drive/folders/1sj2B1eDXigpvvev8Bzckoh8d14xHdYvY	Falha	gerar_documento_cliente() missing 3 required positional arguments: 'dados_cliente', 'id_pasta_cliente', and 'tipo_pessoa'
15	2025-06-22 13:15:28.051193	task-6616ab3b-bb03-4e13-801d-e870f92cb6f6	pf	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	https://drive.google.com/drive/folders/1sj2B1eDXigpvvev8Bzckoh8d14xHdYvY	Falha	gerar_documento_cliente() missing 3 required positional arguments: 'dados_cliente', 'id_pasta_cliente', and 'tipo_pessoa'
16	2025-06-22 13:17:19.868957	task-7ca13fc5-dd0d-4cdf-b4af-4e1fdc52763d	pf	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	https://drive.google.com/drive/folders/1sj2B1eDXigpvvev8Bzckoh8d14xHdYvY	Falha	gerar_documento_cliente() missing 3 required positional arguments: 'dados_cliente', 'id_pasta_cliente', and 'tipo_pessoa'
22	2025-06-23 02:22:49.738478	task-1d78d86f-8591-4376-a076-80ca6a68802b	pf	\N	\N	000.000.000-00	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/1J8jYLA3_3m7OUqU3ZGMuYxOffrMjMkuH	Falha	<HttpError 404 when requesting https://www.googleapis.com/drive/v3/files/1-aBcDeFgHiJkLmNoPqRsTuVwXyZ/copy?fields=id&supportsAllDrives=true&alt=json returned "File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.". Details: "[{'message': 'File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.', 'domain': 'global', 'reason': 'notFound', 'location': 'fileId', 'locationType': 'parameter'}]">
20	2025-06-22 13:37:43.314094	task-9907870b-0942-4995-8c69-31bf047d18a8	pf	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	https://drive.google.com/drive/folders/1sj2B1eDXigpvvev8Bzckoh8d14xHdYvY	Processando	\N
18	2025-06-22 13:24:56.146594	task-4ac0d2aa-acd1-43bb-88e6-b46edcfd337d	pf	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	https://drive.google.com/drive/folders/1sj2B1eDXigpvvev8Bzckoh8d14xHdYvY	Concluido	{"links": []}
21	2025-06-23 02:18:00.029495	task-b7b3d28c-b03e-4274-89d8-9d5d96e96ee7	pf	\N	\N	000.000.000-00	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/1J8jYLA3_3m7OUqU3ZGMuYxOffrMjMkuH	Falha	<HttpError 404 when requesting https://www.googleapis.com/drive/v3/files/1-aBcDeFgHiJkLmNoPqRsTuVwXyZ/copy?fields=id&supportsAllDrives=true&alt=json returned "File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.". Details: "[{'message': 'File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.', 'domain': 'global', 'reason': 'notFound', 'location': 'fileId', 'locationType': 'parameter'}]">
23	2025-06-23 02:38:40.451491	task-71c8129c-b5f8-4098-afe1-7bee2007dbff	pf	\N	\N	000.000.000-00	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/1gkfWUlRXFtc3UsQuQLJn3qfFRY6E7wcq	Falha	<HttpError 404 when requesting https://www.googleapis.com/drive/v3/files/1-aBcDeFgHiJkLmNoPqRsTuVwXyZ/copy?fields=id&supportsAllDrives=true&alt=json returned "File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.". Details: "[{'message': 'File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.', 'domain': 'global', 'reason': 'notFound', 'location': 'fileId', 'locationType': 'parameter'}]">
24	2025-06-23 02:43:15.93673	task-2473c6a2-e105-48e1-b207-0d86b41ffea7	pf	\N	\N	000.000.000-00	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/1gkfWUlRXFtc3UsQuQLJn3qfFRY6E7wcq	Falha	<HttpError 404 when requesting https://www.googleapis.com/drive/v3/files/1-aBcDeFgHiJkLmNoPqRsTuVwXyZ/copy?fields=id&supportsAllDrives=true&alt=json returned "File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.". Details: "[{'message': 'File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.', 'domain': 'global', 'reason': 'notFound', 'location': 'fileId', 'locationType': 'parameter'}]">
25	2025-06-23 02:44:23.260153	task-da4b8452-5c99-4328-a554-4ce064dcfb27	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/1gkfWUlRXFtc3UsQuQLJn3qfFRY6E7wcq	Falha	<HttpError 404 when requesting https://www.googleapis.com/drive/v3/files/1-aBcDeFgHiJkLmNoPqRsTuVwXyZ/copy?fields=id&supportsAllDrives=true&alt=json returned "File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.". Details: "[{'message': 'File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.', 'domain': 'global', 'reason': 'notFound', 'location': 'fileId', 'locationType': 'parameter'}]">
26	2025-06-23 02:47:04.204098	task-4a1ce8e4-3d5e-413e-a7c1-aa375cd090bb	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/1gkfWUlRXFtc3UsQuQLJn3qfFRY6E7wcq	Falha	<HttpError 404 when requesting https://www.googleapis.com/drive/v3/files/1-aBcDeFgHiJkLmNoPqRsTuVwXyZ/copy?fields=id&supportsAllDrives=true&alt=json returned "File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.". Details: "[{'message': 'File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.', 'domain': 'global', 'reason': 'notFound', 'location': 'fileId', 'locationType': 'parameter'}]">
42	2025-06-23 20:47:56.483631	task-df391ccc-7fb2-4f04-8744-74e7789ee1b5	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	joao.silva@teste.com	\N	\N	https://drive.google.com/drive/folders/1BK8qsAZT7qXF6ftNKMWZUN07qZU0mY5O	Concluido	{"links": []}
45	2025-06-23 20:51:34.071034	task-0aaa87cf-381a-401f-8b41-6970bbf5dd88	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	joao.silva@teste.com	\N	\N	https://drive.google.com/drive/folders/1BK8qsAZT7qXF6ftNKMWZUN07qZU0mY5O	Concluido	{"links": []}
27	2025-06-23 02:48:16.126945	task-7cf1cdc7-e7a5-464e-acef-c5079c94866f	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/1gkfWUlRXFtc3UsQuQLJn3qfFRY6E7wcq	Falha	<HttpError 404 when requesting https://www.googleapis.com/drive/v3/files/1-aBcDeFgHiJkLmNoPqRsTuVwXyZ/copy?fields=id&supportsAllDrives=true&alt=json returned "File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.". Details: "[{'message': 'File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.', 'domain': 'global', 'reason': 'notFound', 'location': 'fileId', 'locationType': 'parameter'}]">
33	2025-06-23 02:59:53.332908	task-dfe4aea1-6b48-4f98-bd18-8652fd5d14fc	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/1M6Go6VDFdNnvsczQUXiM2pqX1IuRPrxg	Concluido	{"links": []}
28	2025-06-23 02:51:00.749664	task-a68cca8c-8f03-4ead-93a7-11d7399ca788	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/1gkfWUlRXFtc3UsQuQLJn3qfFRY6E7wcq	Falha	<HttpError 404 when requesting https://www.googleapis.com/drive/v3/files/1-aBcDeFgHiJkLmNoPqRsTuVwXyZ/copy?fields=id&supportsAllDrives=true&alt=json returned "File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.". Details: "[{'message': 'File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.', 'domain': 'global', 'reason': 'notFound', 'location': 'fileId', 'locationType': 'parameter'}]">
29	2025-06-23 02:53:01.359543	task-d7cc8000-a4a5-469e-af00-7e12b6b7d24c	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/1hx-lOvIXGJjBLiuxXLcOwQQXkdRTXGua	Falha	<HttpError 404 when requesting https://www.googleapis.com/drive/v3/files/1-aBcDeFgHiJkLmNoPqRsTuVwXyZ/copy?fields=id&supportsAllDrives=true&alt=json returned "File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.". Details: "[{'message': 'File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.', 'domain': 'global', 'reason': 'notFound', 'location': 'fileId', 'locationType': 'parameter'}]">
34	2025-06-23 03:01:56.049398	task-c2d71eec-d6c7-467c-bf13-f2a8ee802e23	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/1W40co-KGSVkS9aR8Hcke9sG_VDU891sH	Concluido	{"links": []}
30	2025-06-23 02:55:53.03456	task-8b41c7b9-4034-4d42-959a-502a2889f741	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/1hx-lOvIXGJjBLiuxXLcOwQQXkdRTXGua	Falha	<HttpError 404 when requesting https://www.googleapis.com/drive/v3/files/1-aBcDeFgHiJkLmNoPqRsTuVwXyZ/copy?fields=id&supportsAllDrives=true&alt=json returned "File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.". Details: "[{'message': 'File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.', 'domain': 'global', 'reason': 'notFound', 'location': 'fileId', 'locationType': 'parameter'}]">
37	2025-06-23 20:43:35.024553	task-b7470161-6a7f-4f9f-937e-683bfb327274	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	joao.silva@teste.com	\N	\N	https://drive.google.com/drive/folders/1BK8qsAZT7qXF6ftNKMWZUN07qZU0mY5O	Concluido	{"links": []}
31	2025-06-23 02:57:32.509841	task-58609a8a-cd75-49b4-a0eb-d2de1c43e466	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/140LxymBrIQQzuNX6fjMpawkwYCiVmrWa	Falha	<HttpError 404 when requesting https://www.googleapis.com/drive/v3/files/1-aBcDeFgHiJkLmNoPqRsTuVwXyZ/copy?fields=id&supportsAllDrives=true&alt=json returned "File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.". Details: "[{'message': 'File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.', 'domain': 'global', 'reason': 'notFound', 'location': 'fileId', 'locationType': 'parameter'}]">
35	2025-06-23 13:04:42.055617	task-57572665-8ffa-4a09-8417-b2a43ede91bb	pf	\N	\N	037.004.859-80	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	rbg2000@hotmail.com	\N	\N	https://drive.google.com/drive/folders/1NXS2rlPlzklS9qTggHu1JiaXgwGRFs9g	Concluido	{"links": []}
32	2025-06-23 02:58:56.902992	task-8f52e214-fd13-4904-b4b7-e1da622205d9	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	teste@teste.com.br	\N	\N	https://drive.google.com/drive/folders/140LxymBrIQQzuNX6fjMpawkwYCiVmrWa	Falha	<HttpError 404 when requesting https://www.googleapis.com/drive/v3/files/1-aBcDeFgHiJkLmNoPqRsTuVwXyZ/copy?fields=id&supportsAllDrives=true&alt=json returned "File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.". Details: "[{'message': 'File not found: 1-aBcDeFgHiJkLmNoPqRsTuVwXyZ.', 'domain': 'global', 'reason': 'notFound', 'location': 'fileId', 'locationType': 'parameter'}]">
43	2025-06-23 20:48:32.125088	task-969a9b8c-92a6-4d40-960a-5fc2bc5a7532	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	joao.silva@teste.com	\N	\N	https://drive.google.com/drive/folders/1BK8qsAZT7qXF6ftNKMWZUN07qZU0mY5O	Concluido	{"links": []}
36	2025-06-23 18:11:53.170165	task-b3839cd9-17e4-44fd-bf88-5cd084ed2d23	pf	\N	\N	027.329.969-71	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	castilhoveiculoslondrina@gmail.com	\N	\N	https://drive.google.com/drive/folders/13kCwt3iPftc2QrqVR2-_1Mf-V6fSxJG_	Concluido	{"links": []}
40	2025-06-23 20:45:56.527725	task-c622c112-3499-4b38-afdb-b2fa78cbaa83	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	joao.silva@teste.com	\N	\N	https://drive.google.com/drive/folders/1BK8qsAZT7qXF6ftNKMWZUN07qZU0mY5O	Concluido	{"links": []}
38	2025-06-23 20:44:04.299347	task-f2d98e48-a5b7-4783-b91e-a053c134c174	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	joao.silva@teste.com	\N	\N	https://drive.google.com/drive/folders/1BK8qsAZT7qXF6ftNKMWZUN07qZU0mY5O	Concluido	{"links": []}
39	2025-06-23 20:44:45.30121	task-91987451-5617-4534-9c86-5b90dbcaa393	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	joao.silva@teste.com	\N	\N	https://drive.google.com/drive/folders/1BK8qsAZT7qXF6ftNKMWZUN07qZU0mY5O	Concluido	{"links": []}
41	2025-06-23 20:46:42.477243	task-03867039-c678-4cb3-b4e3-af3d947b77b8	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	joao.silva@teste.com	\N	\N	https://drive.google.com/drive/folders/1BK8qsAZT7qXF6ftNKMWZUN07qZU0mY5O	Concluido	{"links": []}
46	2025-06-23 20:53:40.193253	task-771d6efe-4a19-4cc8-be65-d95ed922aae6	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	joao.silva@teste.com	\N	\N	https://drive.google.com/drive/folders/1BK8qsAZT7qXF6ftNKMWZUN07qZU0mY5O	Concluido	{"links": []}
44	2025-06-23 20:50:48.936205	task-747d6ff5-6605-49a1-82dc-0c071c340201	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	joao.silva@teste.com	\N	\N	https://drive.google.com/drive/folders/1BK8qsAZT7qXF6ftNKMWZUN07qZU0mY5O	Concluido	{"links": []}
47	2025-06-23 20:54:26.459886	task-b5022c9d-787b-4213-b699-17b088981a0e	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	joao.silva@teste.com	\N	\N	https://drive.google.com/drive/folders/1BK8qsAZT7qXF6ftNKMWZUN07qZU0mY5O	Concluido	{"links": []}
48	2025-06-23 21:00:03.968519	task-5fe689cc-a400-4e98-82a4-7e8ce3cb59ee	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	joao.silva@teste.com	\N	\N	https://drive.google.com/drive/folders/1BK8qsAZT7qXF6ftNKMWZUN07qZU0mY5O	Concluido	{"links": []}
49	2025-06-23 21:02:36.187911	task-6e76c05e-2712-4be1-a1cb-afd38b3223ba	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	joao.silva@teste.com	\N	\N	https://drive.google.com/drive/folders/1BK8qsAZT7qXF6ftNKMWZUN07qZU0mY5O	Concluido	{"links": []}
50	2025-06-23 21:25:33.762701	task-d84b43df-61f8-49cf-8754-784d1a396630	pf	\N	\N	000.000.000-00	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	teste@email.com	\N	\N	https://drive.google.com/drive/folders/16HQUYQyDxj3Tnx6G6r5U8KoyVB3S1wQj	Concluido	{"links": []}
51	2025-06-24 01:17:21.450294	task-04325f8c-89f8-4786-8071-48f7ea413ae9	pf	\N	\N	12345678901	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	\N	joao.silva@teste.com	\N	\N	https://drive.google.com/drive/folders/1BK8qsAZT7qXF6ftNKMWZUN07qZU0mY5O	Concluido	{"links": []}
\.


--
-- Data for Name: users_peticionador; Type: TABLE DATA; Schema: public; Owner: form_user
--

COPY public.users_peticionador (id, email, password_hash, name, is_active) FROM stdin;
1	fabricionext@gmail.com	pbkdf2:sha256:260000$X3XySfV7t0VfiJ9x$3889e7acfdf42779d2b94bd5b57ddcef293330a91ca7f37463b2c602d738e3aa	\N	t
\.


--
-- Name: __drizzle_migrations_id_seq; Type: SEQUENCE SET; Schema: drizzle; Owner: form_user
--

SELECT pg_catalog.setval('drizzle.__drizzle_migrations_id_seq', 1, true);


--
-- Name: autoridades_transito_id_seq; Type: SEQUENCE SET; Schema: public; Owner: form_user
--

SELECT pg_catalog.setval('public.autoridades_transito_id_seq', 1, false);


--
-- Name: clientes_peticionador_id_seq; Type: SEQUENCE SET; Schema: public; Owner: form_user
--

SELECT pg_catalog.setval('public.clientes_peticionador_id_seq', 2, true);


--
-- Name: document_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: form_user
--

SELECT pg_catalog.setval('public.document_templates_id_seq', 1, false);


--
-- Name: formulario_gerado_id_seq; Type: SEQUENCE SET; Schema: public; Owner: form_user
--

SELECT pg_catalog.setval('public.formulario_gerado_id_seq', 1, false);


--
-- Name: formularios_gerados_id_seq; Type: SEQUENCE SET; Schema: public; Owner: form_user
--

SELECT pg_catalog.setval('public.formularios_gerados_id_seq', 10, true);


--
-- Name: peticao_modelos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: form_user
--

SELECT pg_catalog.setval('public.peticao_modelos_id_seq', 1, true);


--
-- Name: peticao_placeholders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: form_user
--

SELECT pg_catalog.setval('public.peticao_placeholders_id_seq', 28, true);


--
-- Name: peticoes_geradas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: form_user
--

SELECT pg_catalog.setval('public.peticoes_geradas_id_seq', 6, true);


--
-- Name: respostas_form_id_seq; Type: SEQUENCE SET; Schema: public; Owner: form_user
--

SELECT pg_catalog.setval('public.respostas_form_id_seq', 51, true);


--
-- Name: users_peticionador_id_seq; Type: SEQUENCE SET; Schema: public; Owner: form_user
--

SELECT pg_catalog.setval('public.users_peticionador_id_seq', 2, true);


--
-- Name: __drizzle_migrations __drizzle_migrations_pkey; Type: CONSTRAINT; Schema: drizzle; Owner: form_user
--

ALTER TABLE ONLY drizzle.__drizzle_migrations
    ADD CONSTRAINT __drizzle_migrations_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: autoridades_transito autoridades_transito_nome_key; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.autoridades_transito
    ADD CONSTRAINT autoridades_transito_nome_key UNIQUE (nome);


--
-- Name: autoridades_transito autoridades_transito_pkey; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.autoridades_transito
    ADD CONSTRAINT autoridades_transito_pkey PRIMARY KEY (id);


--
-- Name: clientes_peticionador clientes_peticionador_cnpj_key; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.clientes_peticionador
    ADD CONSTRAINT clientes_peticionador_cnpj_key UNIQUE (cnpj);


--
-- Name: clientes_peticionador clientes_peticionador_cpf_key; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.clientes_peticionador
    ADD CONSTRAINT clientes_peticionador_cpf_key UNIQUE (cpf);


--
-- Name: clientes_peticionador clientes_peticionador_email_key; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.clientes_peticionador
    ADD CONSTRAINT clientes_peticionador_email_key UNIQUE (email);


--
-- Name: clientes_peticionador clientes_peticionador_pkey; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.clientes_peticionador
    ADD CONSTRAINT clientes_peticionador_pkey PRIMARY KEY (id);


--
-- Name: document_templates document_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.document_templates
    ADD CONSTRAINT document_templates_pkey PRIMARY KEY (id);


--
-- Name: formularios_gerados formularios_gerados_pkey; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.formularios_gerados
    ADD CONSTRAINT formularios_gerados_pkey PRIMARY KEY (id);


--
-- Name: formularios_gerados formularios_gerados_slug_key; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.formularios_gerados
    ADD CONSTRAINT formularios_gerados_slug_key UNIQUE (slug);


--
-- Name: peticao_modelos peticao_modelos_pkey; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.peticao_modelos
    ADD CONSTRAINT peticao_modelos_pkey PRIMARY KEY (id);


--
-- Name: peticao_placeholders peticao_placeholders_pkey; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.peticao_placeholders
    ADD CONSTRAINT peticao_placeholders_pkey PRIMARY KEY (id);


--
-- Name: peticoes_geradas peticoes_geradas_pkey; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.peticoes_geradas
    ADD CONSTRAINT peticoes_geradas_pkey PRIMARY KEY (id);


--
-- Name: formulario_gerado pk_formulario_gerado; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.formulario_gerado
    ADD CONSTRAINT pk_formulario_gerado PRIMARY KEY (id);


--
-- Name: respostas_form respostas_form_pkey; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.respostas_form
    ADD CONSTRAINT respostas_form_pkey PRIMARY KEY (id);


--
-- Name: respostas_form respostas_form_submission_id_key; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.respostas_form
    ADD CONSTRAINT respostas_form_submission_id_key UNIQUE (submission_id);


--
-- Name: users_peticionador users_peticionador_email_key; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.users_peticionador
    ADD CONSTRAINT users_peticionador_email_key UNIQUE (email);


--
-- Name: users_peticionador users_peticionador_pkey; Type: CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.users_peticionador
    ADD CONSTRAINT users_peticionador_pkey PRIMARY KEY (id);


--
-- Name: formulario_gerado fk_formulario_gerado_cliente_id_clientes_peticionador; Type: FK CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.formulario_gerado
    ADD CONSTRAINT fk_formulario_gerado_cliente_id_clientes_peticionador FOREIGN KEY (cliente_id) REFERENCES public.clientes_peticionador(id);


--
-- Name: formulario_gerado fk_formulario_gerado_modelo_id_peticao_modelos; Type: FK CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.formulario_gerado
    ADD CONSTRAINT fk_formulario_gerado_modelo_id_peticao_modelos FOREIGN KEY (modelo_id) REFERENCES public.peticao_modelos(id);


--
-- Name: formularios_gerados formularios_gerados_modelo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.formularios_gerados
    ADD CONSTRAINT formularios_gerados_modelo_id_fkey FOREIGN KEY (modelo_id) REFERENCES public.peticao_modelos(id);


--
-- Name: peticao_placeholders peticao_placeholders_modelo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.peticao_placeholders
    ADD CONSTRAINT peticao_placeholders_modelo_id_fkey FOREIGN KEY (modelo_id) REFERENCES public.peticao_modelos(id);


--
-- Name: peticoes_geradas peticoes_geradas_cliente_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: form_user
--

ALTER TABLE ONLY public.peticoes_geradas
    ADD CONSTRAINT peticoes_geradas_cliente_id_fkey FOREIGN KEY (cliente_id) REFERENCES public.clientes_peticionador(id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: pg_database_owner
--

GRANT ALL ON SCHEMA public TO form_user;


--
-- PostgreSQL database dump complete
--

