-- db.sql

-- Enable unaccent and pg_trgm extensions
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS pieces (
  sap VARCHAR PRIMARY KEY,
  categoria VARCHAR NOT NULL,
  descricao VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS availability (
  sap VARCHAR REFERENCES pieces(sap),
  data DATE NOT NULL,
  hora INT NOT NULL,
  ocupado BOOLEAN NOT NULL,
  PRIMARY KEY (sap, data, hora)
);

-- Insert all items into the pieces table
INSERT INTO pieces (sap, categoria, descricao) VALUES
('MAT001', 'Ferramentas de Corte', 'Serra Circular'),
('MAT002', 'Ferramentas de Corte', 'Disco de Corte'),
('MAT003', 'Ferramentas de Corte', 'Serra de Fita'),
('MAT004', 'Ferramentas de Corte', 'Disco de Desbaste'),
('MAT005', 'Ferramentas de Corte', 'Broca de Aço Rápido 10mm'),
('MAT006', 'Ferramentas de Corte', 'Conjunto de Fresas para Usinagem'),
('MAT007', 'Ferramentas de Corte', 'Lâmina de Serra Sabre'),
('EQP001', 'Ferramentas de Corte', 'Lixadeira Angular'),
('MAT101', 'Ferramentas de Medição', 'Paquímetro Digital'),
('MAT102', 'Ferramentas de Medição', 'Micrômetro'),
('MAT103', 'Ferramentas de Medição', 'Relógio Comparador'),
('MAT104', 'Ferramentas de Medição', 'Trena de Aço 5m'),
('MAT105', 'Ferramentas de Medição', 'Nível de Bolha'),
('MAT106', 'Ferramentas de Medição', 'Goniômetro Digital'),
('MAT107', 'Ferramentas de Medição', 'Manômetro para Pressão'),
('MAT108', 'Ferramentas de Medição', 'Calibrador de Roscas'),
('EQP201', 'Equipamentos de Solda', 'Máquina de Solda MIG'),
('MAT201', 'Equipamentos de Solda', 'Eletrodo de Solda Inox'),
('MAT202', 'Equipamentos de Solda', 'Máscara de Solda Automática'),
('EQP202', 'Equipamentos de Solda', 'Maçarico de Corte Oxiacetilênico'),
('MAT203', 'Equipamentos de Solda', 'Tocha de Solda TIG'),
('MAT204', 'Equipamentos de Solda', 'Fio de Solda MIG ER70S-6'),
('MAT205', 'Equipamentos de Solda', 'Regulador de Pressão para Gás'),
('MAT206', 'Equipamentos de Solda', 'Tubo de Gás Acetileno'),
('MAT301', 'Lubrificação e Manutenção', 'Graxa Industrial'),
('MAT302', 'Lubrificação e Manutenção', 'Óleo Lubrificante 10W30'),
('EQP301', 'Lubrificação e Manutenção', 'Bomba de Graxa Pneumática'),
('MAT303', 'Lubrificação e Manutenção', 'Limpa Contatos Elétricos'),
('MAT304', 'Lubrificação e Manutenção', 'Spray Desengripante'),
('MAT305', 'Lubrificação e Manutenção', 'Veda Rosca em Fita'),
('MAT401', 'Equipamentos de Segurança', 'Capacete de Segurança com Aba'),
('MAT402', 'Equipamentos de Segurança', 'Luvas Térmicas de Alta Resistência'),
('MAT403', 'Equipamentos de Segurança', 'Óculos de Proteção Antirrespingos'),
('MAT404', 'Equipamentos de Segurança', 'Protetor Auricular Tipo Plug'),
('MAT405', 'Equipamentos de Segurança', 'Máscara Respiratória com Filtro P3'),
('MAT406', 'Equipamentos de Segurança', 'Cinto de Segurança para Trabalho em Altura'),
('MAT407', 'Equipamentos de Segurança', 'Sapato de Segurança com Biqueira de Aço'),
('MAT408', 'Equipamentos de Segurança', 'Protetor Facial de Policarbonato'),
('EQP501', 'Equipamentos de Elevação', 'Talha Elétrica de Corrente'),
('MAT501', 'Equipamentos de Elevação', 'Corrente de Elevação de 10m'),
('MAT502', 'Equipamentos de Elevação', 'Gancho Giratório com Trava de Segurança'),
('MAT503', 'Equipamentos de Elevação', 'Cinta de Elevação com Olhal'),
('EQP502', 'Equipamentos de Elevação', 'Carrinho de Transporte de Bobinas'),
('EQP503', 'Equipamentos de Elevação', 'Macaco Hidráulico 10 Toneladas'),
('MAT601', 'Componentes Mecânicos', 'Rolamento Esférico de Precisão'),
('MAT602', 'Componentes Mecânicos', 'Parafuso de Alta Resistência M12'),
('MAT603', 'Componentes Mecânicos', 'Correia de Transmissão Industrial'),
('MAT604', 'Componentes Mecânicos', 'Junta de Vedação em Borracha'),
('MAT605', 'Componentes Mecânicos', 'Engrenagem Cilíndrica de Aço'),
('MAT606', 'Componentes Mecânicos', 'Bucha de Bronze Autolubrificante'),
('MAT607', 'Componentes Mecânicos', 'Eixo de Transmissão'),
('MAT608', 'Componentes Mecânicos', 'Polia de Alumínio'),
('EQP601', 'Equipamentos Hidráulicos', 'Válvula Solenoide Hidráulica'),
('EQP602', 'Equipamentos Hidráulicos', 'Bomba Hidráulica de Pistão'),
('MAT701', 'Equipamentos Hidráulicos', 'Mangueira Hidráulica de Alta Pressão'),
('MAT702', 'Equipamentos Hidráulicos', 'Conector Hidráulico Rápido'),
('EQP701', 'Equipamentos Elétricos', 'Motor Elétrico Trifásico 5HP'),
('MAT801', 'Equipamentos Elétricos', 'Cabo Elétrico 10mm²'),
('MAT802', 'Equipamentos Elétricos', 'Disjuntor de 100A'),
('EQP702', 'Equipamentos Elétricos', 'Quadro de Comando Elétrico com Inversor de Frequência'),
('MAT803', 'Equipamentos Elétricos', 'Chave Seccionadora'),
('MAT804', 'Equipamentos Elétricos', 'Fusível NH 100A'),
('MAT805', 'Equipamentos Elétricos', 'Tomada Industrial 380V'),
('MAT901', 'Ferramentas Manuais', 'Chave de Fenda Phillips 6mm'),
('MAT902', 'Ferramentas Manuais', 'Alicate de Corte'),
('MAT903', 'Ferramentas Manuais', 'Martelo de Borracha'),
('MAT904', 'Ferramentas Manuais', 'Torquímetro 40-200Nm'),
('MAT905', 'Ferramentas Manuais', 'Conjunto de Chaves Allen'),
('MAT906', 'Ferramentas Manuais', 'Chave Estrela 12mm'),
('MAT907', 'Ferramentas Manuais', 'Serra Manual')
ON CONFLICT (sap) DO NOTHING;


-- Insert limited availability with at least one busy hour for each piece for today and tomorrow

INSERT INTO availability (sap, data, hora, ocupado) VALUES
-- Availability for today
('MAT001', CURRENT_DATE, 5, TRUE),
('MAT002', CURRENT_DATE, 6, TRUE),
('MAT003', CURRENT_DATE, 7, TRUE),
('MAT004', CURRENT_DATE, 8, TRUE),
('MAT005', CURRENT_DATE, 9, TRUE),
('MAT006', CURRENT_DATE, 10, TRUE),
('MAT007', CURRENT_DATE, 11, TRUE),
('EQP001', CURRENT_DATE, 12, TRUE),
('MAT101', CURRENT_DATE, 13, TRUE),
('MAT102', CURRENT_DATE, 14, TRUE),
('MAT103', CURRENT_DATE, 15, TRUE),
('MAT104', CURRENT_DATE, 16, TRUE),
('MAT105', CURRENT_DATE, 17, TRUE),
('MAT106', CURRENT_DATE, 18, TRUE),
('MAT107', CURRENT_DATE, 19, TRUE),
('MAT108', CURRENT_DATE, 20, TRUE),
('EQP201', CURRENT_DATE, 21, TRUE),
('MAT201', CURRENT_DATE, 22, TRUE),
('MAT202', CURRENT_DATE, 23, TRUE),
('EQP202', CURRENT_DATE, 24, TRUE),

-- Availability for tomorrow
('MAT001', CURRENT_DATE + 1, 5, TRUE),
('MAT002', CURRENT_DATE + 1, 6, TRUE),
('MAT003', CURRENT_DATE + 1, 7, TRUE),
('MAT004', CURRENT_DATE + 1, 8, TRUE),
('MAT005', CURRENT_DATE + 1, 9, TRUE),
('MAT006', CURRENT_DATE + 1, 10, TRUE),
('MAT007', CURRENT_DATE + 1, 11, TRUE),
('EQP001', CURRENT_DATE + 1, 12, TRUE),
('MAT101', CURRENT_DATE + 1, 13, TRUE),
('MAT102', CURRENT_DATE + 1, 14, TRUE),
('MAT103', CURRENT_DATE + 1, 15, TRUE),
('MAT104', CURRENT_DATE + 1, 16, TRUE),
('MAT105', CURRENT_DATE + 1, 17, TRUE),
('MAT106', CURRENT_DATE + 1, 18, TRUE),
('MAT107', CURRENT_DATE + 1, 19, TRUE),
('MAT108', CURRENT_DATE + 1, 20, TRUE),
('EQP201', CURRENT_DATE + 1, 21, TRUE),
('MAT201', CURRENT_DATE + 1, 22, TRUE),
('MAT202', CURRENT_DATE + 1, 23, TRUE),
('EQP202', CURRENT_DATE + 1, 24, TRUE)
ON CONFLICT (sap, data, hora) DO NOTHING;
