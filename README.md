# ☁️ Cloud Janitor — Automação Inteligente para Redução de Desperdício Financeiro na AWS

<p align="center">
  <img src="./images/arquitetura-cloud-janitor.png" alt="Arquitetura do Cloud Janitor" width="800"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/AWS-Cloud-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white"/>
  <img src="https://img.shields.io/badge/AWS_Lambda-Serverless-F90?style=for-the-badge&logo=awslambda&logoColor=white"/>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Boto3-AWS_SDK-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white"/>
  <img src="https://img.shields.io/badge/FinOps-Cost_Optimization-00C853?style=for-the-badge"/>
</p>

---

## 📋 Índice

- [Descrição do Projeto](#-descrição-do-projeto)
- [Problema de Negócio](#-problema-de-negócio)
- [Solução Proposta](#-solução-proposta)
- [Arquitetura e Serviços Utilizados](#️-arquitetura-e-serviços-utilizados)
- [Lógica de Funcionamento](#-lógica-de-funcionamento)
- [Código da Função Lambda](#-código-da-função-lambda)
- [Passo a Passo de Configuração](#-passo-a-passo-de-configuração)
- [Exemplo de Cenário](#-exemplo-de-cenário)
- [Resultado Esperado](#-resultado-esperado)
- [Benefícios do Projeto](#-benefícios-do-projeto)
- [Possíveis Melhorias Futuras](#-possíveis-melhorias-futuras)
- [Aprendizados Aplicados](#-aprendizados-aplicados)
- [Conclusão](#-conclusão)

---

## 📌 Descrição do Projeto

O **Cloud Janitor** é uma automação serverless criada para **reduzir desperdício financeiro em ambientes AWS**.

A solução utiliza **AWS Lambda + Python + Boto3** para identificar instâncias **EC2 em execução** e desligar automaticamente apenas aquelas que:

- ❌ **não estão marcadas como produção**
- ✅ possuem a tag **`AutoStop=true`**

O objetivo é evitar custos desnecessários com ambientes de **desenvolvimento, homologação ou teste** que permanecem ligados fora do horário de uso.

---

## 🚨 Problema de Negócio

Em muitas empresas, desenvolvedores e equipes técnicas criam instâncias EC2 para testes, validações e ambientes temporários. Esses recursos nem sempre são desligados ao final do expediente, permanecendo ativos durante a madrugada, finais de semana e feriados.

Isso gera:

| Problema | Impacto |
|---|---|
| Instâncias ligadas sem uso | Aumento de custo desnecessário |
| Falta de controle sobre ambientes | Baixa governança operacional |
| Recursos ociosos em nuvem | Desperdício financeiro |
| Sem padrão de desligamento | Imprevisibilidade nos custos |

---

## 💡 Solução Proposta

Para resolver esse problema, foi criada uma **automação baseada em eventos**:

```
EventBridge Scheduler → Lambda (Python/Boto3) → EC2 (avalia tags) → Desliga instâncias elegíveis → CloudWatch Logs
```

**Fluxo detalhado:**

1. O **EventBridge Scheduler** agenda a execução da automação em horários definidos
2. A **AWS Lambda** executa o script em Python
3. O **Boto3** consulta a API da AWS buscando instâncias EC2 em estado `running`
4. As **tags** de cada instância são analisadas
5. Instâncias de **produção** são ignoradas e protegidas
6. Instâncias com **`AutoStop=true`** são desligadas automaticamente
7. Toda a execução é registrada no **CloudWatch Logs**

---

## 🏗️ Arquitetura e Serviços Utilizados

<p align="center">
  <img src="./images/diagrama-arquitetura.png" alt="Diagrama de Arquitetura" width="750"/>
</p>

### Serviços AWS

| Serviço | Função |
|---|---|
| **AWS Lambda** | Executa o script Python de automação |
| **Amazon EC2** | Recurso monitorado e controlado pela automação |
| **IAM Role / IAM Policy** | Garante o menor privilégio necessário para a Lambda |
| **Amazon EventBridge Scheduler** | Dispara a Lambda de forma agendada e recorrente |
| **Amazon CloudWatch Logs** | Armazena e centraliza os logs de execução |
| **CloudWatch Billing Alarm** | Monitora custos estimados e evita gastos inesperados |
| **Amazon SNS** | Envia notificações de alerta por e-mail |

---

## 🔎 Lógica de Funcionamento

A automação foi construída com base em **duas tags principais**:

### Tag de ambiente
```
Ambiente = Producao
```
> Se a instância estiver marcada como produção, ela **não será desligada**.

### Tag de autorização para desligamento automático
```
AutoStop = true
```
> Se a instância **não for produção** e possuir `AutoStop=true`, ela **será desligada**.

### Regras de Decisão

```
┌─────────────────────────────────────────────────────────┐
│                  Instância EC2 running                  │
└────────────────────────┬────────────────────────────────┘
                         │
              Ambiente = Producao?
             /                    \
           SIM                    NÃO
            │                      │
         IGNORAR           AutoStop = true?
                          /               \
                        SIM              NÃO
                         │                │
                      DESLIGAR         IGNORAR
```

---

## 🐍 Código da Função Lambda

```python
import boto3

def lambda_handler(event, context):
    ec2 = boto3.resource('ec2')
    
    # Filtra apenas instâncias que estão ligadas
    instances = ec2.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
    )

    instancias_desligadas = []
    instancias_ignoradas = []

    for instance in instances:
        # Transforma as tags em dicionário para facilitar a leitura
        tags = {tag['Key']: tag['Value'] for tag in instance.tags} if instance.tags else {}

        ambiente = tags.get('Ambiente')
        auto_stop = tags.get('AutoStop')

        # Regra 1: se for produção, não desliga
        if ambiente == 'Producao':
            instancias_ignoradas.append(f'{instance.id} - ignorada por ser produção')
            continue

        # Regra 2: só desliga se tiver AutoStop=true
        if auto_stop != 'true':
            instancias_ignoradas.append(f'{instance.id} - ignorada por não ter AutoStop=true')
            continue

        # Se passou nas regras, desliga a instância
        instance.stop()
        instancias_desligadas.append(instance.id)
        print(f'Instância {instance.id} desligada com sucesso.')

    return {
        'statusCode': 200,
        'body': {
            'mensagem': 'Execução concluída com sucesso.',
            'instancias_desligadas': instancias_desligadas,
            'instancias_ignoradas': instancias_ignoradas
        }
    }
```

---

## 🚀 Passo a Passo de Configuração

### 1️⃣ Criar o Billing Alarm

Antes de iniciar, configure um **Billing Alarm** para monitorar custos e evitar surpresas.

**Configuração adotada:**
- Limite de alerta: **US$ 03,00**
- Notificação por e-mail via **SNS**

Selecione a métrica: 

| <img width="1918" height="870" alt="image" src="https://github.com/user-attachments/assets/b78f6ce8-d659-4c67-ab39-25547ce2de05" />|
|-------------------------------------------------------------------------------------------------------------------------|
| *Figura - Adicionando métrica para o alarme*|

Selecione o tópico do SNS ou faça um caso ainda não tenha:

| <img width="1896" height="728" alt="image" src="https://github.com/user-attachments/assets/22b1e88b-8c56-4718-8141-a61b798eaa42" /> |
|-------------------------------------------------------------------------------------------------------------------------|
| *Figura - Adicionando SNS* |

Define o limite do valor e a condição do seu alarme:

| <img width="1902" height="748" alt="image" src="https://github.com/user-attachments/assets/0864876d-b984-4b1f-89a2-e8b8480dfa48" /> |
|-------------------------------------------------------------------------------------------------------------------------|
| *Figura - Condições* |

Adicione o nome e uma descrição se quiser:

| <img width="1894" height="657" alt="image" src="https://github.com/user-attachments/assets/5a3b4051-d9b2-4217-b34b-c972e466d704" /> |
|-------------------------------------------------------------------------------------------------------------------------|
| *Figura - Nome e descrição* |

---

### 2️⃣ Criar a IAM Policy Customizada

Crie uma policy com **permissões mínimas** para a Lambda (princípio do menor privilégio):

```json
{
  "Version": "2012-10-17",
  "Statement": [ 
    {
      "Sid": "DescribeAndStopEC2",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:StopInstances"
      ],
      "Resource": "*"
    }
  ]
}
```

---

### 3️⃣ Criar a IAM Role da Lambda

Crie uma role específica para a função Lambda com:

- Trust relationship para `lambda.amazonaws.com`
- Policy customizada de EC2
- `AWSLambdaBasicExecutionRole` para permissão de logs

| <img width="1896" height="805" alt="image" src="https://github.com/user-attachments/assets/cd60a1c6-bf66-4e54-b502-bc739a0efc86" />|
|-------------------------------------------------------------------------------------------------------------------------|
| *Figura - Nome e descrição* |

| <img width="1899" height="561" alt="image" src="https://github.com/user-attachments/assets/d86c26b5-906c-4d6b-9194-6d0bcb4ae98c" /> |
|-------------------------------------------------------------------------------------------------------------------------|
| *Figura - Nome e descrição* |

| <img width="1895" height="760" alt="image" src="https://github.com/user-attachments/assets/e534e19c-1001-4da5-9c02-c38e21ce687b" /> |
|-------------------------------------------------------------------------------------------------------------------------|
| *Figura - Nome e descrição* |

---

### 4️⃣ Criar a Função Lambda

| Configuração | Valor |
|---|---|
| Nome | `cloud-janitor-ec2-auto-stop` |
| Runtime | Python 3.14 |
| Arquitetura | x86_64 |
| Role | CloudJanitorLambdaRole |


| <img width="1541" height="753" alt="image" src="https://github.com/user-attachments/assets/464619f0-bfa7-46e6-80d0-931bc8d729ec" /> |
|-------------------------------------------------------------------------------------------------------------------------|
| *Figura - Nome e descrição* |


---

### 5️⃣ Inserir o Código Python

Cole o código da função no editor da Lambda e faça o **Deploy**.


| <img width="1540" height="756" alt="image" src="https://github.com/user-attachments/assets/da2cf60a-becc-4b9d-8cae-a3955008c092" /> |
|-------------------------------------------------------------------------------------------------------------------------|
| *Figura - Nome e descrição* |

---

### 6️⃣ Configurar as Tags na Instância EC2

Configure as tags nas instâncias conforme a regra de negócio:

| Tag | Valor | Comportamento |
|---|---|---|
| `Ambiente` | `Producao` | Instância **protegida**, nunca será desligada |
| `Ambiente` | `Dev` / `Teste` / qualquer outro | Elegível para avaliação |
| `AutoStop` | `true` | Instância **será desligada** (se não for produção) |


| <img width="1900" height="661" alt="image" src="https://github.com/user-attachments/assets/63c33100-944e-4c40-9245-03e12620fdfa" /> |
|-------------------------------------------------------------------------------------------------------------------------|
| *Figura - Nome e descrição* |


---

### 7️⃣ Testar a Lambda Manualmente

Execute um teste manual com o evento:

```json
{}
```

O teste valida:
- ✅ Acesso à EC2
- ✅ Leitura das tags
- ✅ Aplicação da regra de negócio
- ✅ Desligamento automático da instância elegível

<p align="center">
  <img src="./images/teste-lambda.png" alt="Teste Manual da Lambda" width="700"/>
</p>

---

### 8️⃣ Validar os Logs no CloudWatch

Após a execução, analise os logs no **CloudWatch** para validar o comportamento da automação.


| <img width="1890" height="751" alt="image" src="https://github.com/user-attachments/assets/bfa6add9-df62-4a19-b566-31a137e5560c" /> |
|-------------------------------------------------------------------------------------------------------------------------|
| *Figura - Nome e descrição* |

---

### 9️⃣ Criar o Agendamento com EventBridge Scheduler

Configure a execução recorrente via **EventBridge Scheduler**.

**Exemplo de uso:** execução diária às `20:00` para desligar ambientes não produtivos ao fim do expediente.

---

## 🧪 Exemplo de Cenário

| Instância | Tags | Resultado |
|---|---|---|
| Instância 1 | `Ambiente=Producao`, `AutoStop=true` | ✅ **Ignorada** — protegida por ser produção |
| Instância 2 | `Ambiente=Dev`, `AutoStop=true` | 🔴 **Desligada** — elegível para auto stop |
| Instância 3 | `Ambiente=Teste` (sem AutoStop) | ✅ **Ignorada** — sem a tag AutoStop=true |

---

## ✅ Resultado Esperado

Ao executar a Lambda, o retorno será semelhante a:

```json
{
  "statusCode": 200,
  "body": {
    "mensagem": "Execução concluída com sucesso.",
    "instancias_desligadas": [
      "i-xxxxxxxxxxxxxxxxx"
    ],
    "instancias_ignoradas": []
  }
}
```

---

## 💰 Benefícios do Projeto

- 📉 Redução de desperdício financeiro em nuvem
- 🤖 Automação de rotina operacional
- 💡 Aplicação prática de **FinOps**
- ☁️ Uso de arquitetura **serverless**
- 🏷️ Controle de ambientes por tags
- 🔐 Governança com princípio do menor privilégio

---

## 🔮 Possíveis Melhorias Futuras

- [ ] Ligar instâncias automaticamente pela manhã
- [ ] Enviar relatório por e-mail com resumo da execução via SNS
- [ ] Adicionar suporte a múltiplas regiões AWS
- [ ] Criar dashboards de monitoramento no CloudWatch
- [ ] Implementar a infraestrutura como código com **Terraform**
- [ ] Expandir a lógica para outros recursos como **RDS**, **ECS tasks**, etc.

---

## 📚 Aprendizados Aplicados

Este projeto permitiu praticar na prática:

- `AWS Lambda` — funções serverless orientadas a eventos
- `Amazon EC2` — gerenciamento e automação de instâncias
- `IAM` — princípio do menor privilégio
- `EventBridge Scheduler` — agendamento de execuções
- `CloudWatch Logs` — observabilidade e rastreabilidade
- `Billing Alarm` — monitoramento de custos
- `Python + Boto3` — automação de infraestrutura AWS
- `FinOps` — otimização de custos em nuvem
- `Governança por tags` — padrão de classificação de recursos

---

## 🏁 Conclusão

O **Cloud Janitor** é uma solução prática de automação serverless com foco em **otimização de custos na AWS**.

A proposta demonstra como pequenas rotinas automatizadas podem gerar ganho real de **governança, previsibilidade e eficiência operacional** em ambientes cloud — sem necessidade de servidores dedicados e com custo operacional praticamente zero.

Além do aspecto técnico, o projeto reforça a importância de práticas de **FinOps**, uso consciente de recursos e automações seguras baseadas em **tags e permissões mínimas**.

---

<p align="center">
  Desenvolvido com ☁️ e 🐍 utilizando AWS Lambda, Python e Boto3
</p>
