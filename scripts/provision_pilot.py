# scripts/provision_pilot.py
import os
import sys
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator
import psycopg2

# 1. Modèle de validation Pydantic pour l'ICP
class ICPConfigSchema(BaseModel):
    client_id: UUID
    nom: str = Field(..., min_length=3, max_length=100)
    description_icp: str = Field(..., min_length=10)
    codes_naf: List[str] = Field(default_factory=list)
    departements: List[str] = Field(default_factory=list)
    effectif_min: int = Field(default=1, ge=0)
    effectif_max: int = Field(default=500)
    anciennete_min_ans: int = Field(default=0, ge=0)
    exiger_site_web: bool = False
    exiger_email: bool = False
    mots_cles_positifs: List[str] = Field(default_factory=list)
    mots_cles_negatifs: List[str] = Field(default_factory=list)

    @field_validator('codes_naf')
    @classmethod
    def validate_naf_format(cls, v: List[str]) -> List[str]:
        for code in v:
            if len(code) != 5 or not code[:4].isdigit() or not code[4].isalpha():
                raise ValueError(f"Le code NAF '{code}' est invalide. Format attendu: 5 caractères (ex: 4520Z)")
        return [code.upper() for code in v]

    @field_validator('departements')
    @classmethod
    def validate_dept_format(cls, v: List[str]) -> List[str]:
        for dept in v:
            if not (len(dept) in [2, 3] and (dept.isdigit() or dept in ["2A", "2B"])):
                raise ValueError(f"Le département '{dept}' est invalide (ex: '75', '2A', '974')")
        return v

    @model_validator(mode='after')
    def validate_effectifs(self) -> 'ICPConfigSchema':
        if self.effectif_max < self.effectif_min:
            raise ValueError("L'effectif maximum doit être supérieur ou égal à l'effectif minimum.")
        return self


def save_icp_to_db(icp: ICPConfigSchema):
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/prospection")
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        query = """
            INSERT INTO criteres_ciblage (
                client_id, nom, description_icp, codes_naf, departements,
                effectif_min, effectif_max, anciennete_min_ans,
                exiger_site_web, exiger_email, mots_cles_positifs, mots_cles_negatifs, actif
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            RETURNING id;
        """
        
        cur.execute(query, (
            str(icp.client_id),
            icp.nom,
            icp.description_icp,
            icp.codes_naf,
            icp.departements,
            icp.effectif_min,
            icp.effectif_max,
            icp.anciennete_min_ans,
            icp.exiger_site_web,
            icp.exiger_email,
            icp.mots_cles_positifs,
            icp.mots_cles_negatifs
        ))
        
        icp_id = cur.fetchone()[0]
        conn.commit()
        print(f"[SUCCESS] Critères d'ICP enregistrés en base avec ID : {icp_id}")
        return icp_id
        
    except Exception as e:
        print(f"[ERROR] Impossible de sauvegarder l'ICP : {e}")
        sys.exit(1)
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()


# 2. Provisioning automatique du client pilote et de son ICP
def provision_pilot_client():
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/prospection")
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO clients (nom_entreprise, secteur, produit_vendu, zone_intervention, statut)
            VALUES ('DistriPièces Auto', 'Automobile', 'Pièces de rechange', 'Régionale', 'actif')
            ON CONFLICT (contact_email) DO UPDATE SET nom_entreprise = EXCLUDED.nom_entreprise
            RETURNING id;
        """)
        client_id = cur.fetchone()[0]
        conn.commit()
        print(f"[INIT] Client pilote 'DistriPièces Auto' vérifié/créé (ID: {client_id})")
        
        pilot_icp = ICPConfigSchema(
            client_id=client_id,
            nom="Garages Indépendants Île-de-France",
            description_icp="Garages indépendants de réparation automobile, hors concessions de grandes marques nationales.",
            codes_naf=["4520Z", "4511Z", "4531Z", "4532Z"],
            departements=["75", "77", "78", "91", "92", "93", "94", "95"],
            effectif_min=2,
            effectif_max=15,
            anciennete_min_ans=3,
            exiger_site_web=False,
            exiger_email=False,
            mots_cles_positifs=["carrosserie", "mécanique", "pneus", "vidange", "garage"],
            mots_cles_negatifs=["concessionnaire", "peugeot", "renault", "citroen", "bmw", "mercedes"]
        )
        
        save_icp_to_db(pilot_icp)
        
    except Exception as e:
        print(f"[ERROR] Échec du provisioning client pilote : {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    provision_pilot_client()