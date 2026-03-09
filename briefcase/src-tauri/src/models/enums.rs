use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
#[serde(rename_all = "kebab-case")]
pub enum Importance {
    Critical,
    Executive,
    #[default]
    Technical,
    Research,
    Approved,
    Archived,
}

impl std::fmt::Display for Importance {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            Importance::Critical => "critical",
            Importance::Executive => "executive",
            Importance::Technical => "technical",
            Importance::Research => "research",
            Importance::Approved => "approved",
            Importance::Archived => "archived",
        };
        write!(f, "{s}")
    }
}

impl std::str::FromStr for Importance {
    type Err = String;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "critical" => Ok(Importance::Critical),
            "executive" => Ok(Importance::Executive),
            "technical" => Ok(Importance::Technical),
            "research" => Ok(Importance::Research),
            "approved" => Ok(Importance::Approved),
            "archived" => Ok(Importance::Archived),
            other => Err(format!("unknown Importance: {other}")),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
#[serde(rename_all = "kebab-case")]
pub enum Audience {
    Executive,
    Engineering,
    Client,
    #[default]
    Internal,
    Public,
}

impl std::fmt::Display for Audience {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            Audience::Executive => "executive",
            Audience::Engineering => "engineering",
            Audience::Client => "client",
            Audience::Internal => "internal",
            Audience::Public => "public",
        };
        write!(f, "{s}")
    }
}

impl std::str::FromStr for Audience {
    type Err = String;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "executive" => Ok(Audience::Executive),
            "engineering" => Ok(Audience::Engineering),
            "client" => Ok(Audience::Client),
            "internal" => Ok(Audience::Internal),
            "public" => Ok(Audience::Public),
            other => Err(format!("unknown Audience: {other}")),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
#[serde(rename_all = "kebab-case")]
pub enum Confidentiality {
    Confidential,
    #[default]
    Internal,
    Unrestricted,
}

impl std::fmt::Display for Confidentiality {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            Confidentiality::Confidential => "confidential",
            Confidentiality::Internal => "internal",
            Confidentiality::Unrestricted => "unrestricted",
        };
        write!(f, "{s}")
    }
}

impl std::str::FromStr for Confidentiality {
    type Err = String;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "confidential" => Ok(Confidentiality::Confidential),
            "internal" => Ok(Confidentiality::Internal),
            "unrestricted" => Ok(Confidentiality::Unrestricted),
            other => Err(format!("unknown Confidentiality: {other}")),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, Default)]
#[serde(rename_all = "kebab-case")]
pub enum VettedStatus {
    #[default]
    Unvetted,
    AiVetted,
    PeerReviewed,
    HumanApproved,
    FinalLocked,
}

impl std::fmt::Display for VettedStatus {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            VettedStatus::Unvetted => "unvetted",
            VettedStatus::AiVetted => "ai-vetted",
            VettedStatus::PeerReviewed => "peer-reviewed",
            VettedStatus::HumanApproved => "human-approved",
            VettedStatus::FinalLocked => "final-locked",
        };
        write!(f, "{s}")
    }
}

impl std::str::FromStr for VettedStatus {
    type Err = String;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "unvetted" => Ok(VettedStatus::Unvetted),
            "ai-vetted" => Ok(VettedStatus::AiVetted),
            "peer-reviewed" => Ok(VettedStatus::PeerReviewed),
            "human-approved" => Ok(VettedStatus::HumanApproved),
            "final-locked" => Ok(VettedStatus::FinalLocked),
            other => Err(format!("unknown VettedStatus: {other}")),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum RelationshipType {
    DerivedFrom,
    Supersedes,
    PresentedIn,
    ReviewedBy,
    RenderedFrom,
    ExportedAs,
    Bundles,
    References,
}

impl std::fmt::Display for RelationshipType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let s = match self {
            RelationshipType::DerivedFrom => "derived-from",
            RelationshipType::Supersedes => "supersedes",
            RelationshipType::PresentedIn => "presented-in",
            RelationshipType::ReviewedBy => "reviewed-by",
            RelationshipType::RenderedFrom => "rendered-from",
            RelationshipType::ExportedAs => "exported-as",
            RelationshipType::Bundles => "bundles",
            RelationshipType::References => "references",
        };
        write!(f, "{s}")
    }
}

impl std::str::FromStr for RelationshipType {
    type Err = String;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "derived-from" => Ok(RelationshipType::DerivedFrom),
            "supersedes" => Ok(RelationshipType::Supersedes),
            "presented-in" => Ok(RelationshipType::PresentedIn),
            "reviewed-by" => Ok(RelationshipType::ReviewedBy),
            "rendered-from" => Ok(RelationshipType::RenderedFrom),
            "exported-as" => Ok(RelationshipType::ExportedAs),
            "bundles" => Ok(RelationshipType::Bundles),
            "references" => Ok(RelationshipType::References),
            other => Err(format!("unknown RelationshipType: {other}")),
        }
    }
}
