from datetime import datetime

from API.infrastructure.database.models import Base

import datetime
import typing
from sqlalchemy import (BigInteger, Column, String, select, Date,
                        DateTime, func, Integer, ForeignKey, Boolean, update,
                        desc, not_, VARCHAR, Text, CHAR, JSON, DECIMAL, FLOAT, DOUBLE)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship


class Vacancies(Base):
    __tablename__ = "vacancies"
    id = Column(String, primary_key=True)
    vacancies_id = Column(String, nullable=True)
    gender = Column(String)
    age_to: Column[String] = Column(String)
    age_from: Column[String] = Column(String)
    salary = Column(FLOAT)
    deal_id = Column(String)
    is_active = Column(Boolean, default=False)

    @classmethod
    async def get_vacancies_by_id(
            cls,
            draft_id: str,
            session: AsyncSession
    ) -> typing.Optional['Vacancies']:
        stmt = select(Vacancies).where(Vacancies.id == draft_id)

        return await session.scalar(stmt)

    @classmethod
    async def get_vacancies(
            cls,
            session: AsyncSession
    ) -> typing.Sequence['Vacancies']:
        stmt = select(Vacancies).where(True == Vacancies.is_active)
        response = await session.execute(stmt)

        return response.scalars().all()

    @classmethod
    async def get_by_id(
            cls,
            session: AsyncSession,
            vacancy_id: str,
    ) -> typing.Optional['Vacancies']:
        stmt = select(Vacancies).where(vacancy_id == Vacancies.vacancies_id)

        return await session.scalar(stmt)


class Token(Base):
    __tablename__ = "tokens"
    id = Column(BigInteger, primary_key=True)
    access_token = Column(String)
    refresh_token = Column(String)

    @classmethod
    async def get_token(
            cls,
            session: AsyncSession
    ):
        stmt = select(Token)
        return await session.scalar(stmt)


class Resumes(Base):
    __tablename__ = 'resumes'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    resume_id = Column(String)
    vacancies_id = Column(
        String,
        ForeignKey("vacancies.id", onupdate="CASCADE", ondelete="CASCADE")
    )

    @classmethod
    async def get_by_resume_id(
            cls,
            session: AsyncSession,
            resume_id: str,
            vacancies_id: str
    ) -> typing.Optional['Resumes']:
        stmt = select(Resumes).where(
            (resume_id == Resumes.resume_id) &
            (Resumes.vacancies_id == vacancies_id))

        return await session.scalar(stmt)
